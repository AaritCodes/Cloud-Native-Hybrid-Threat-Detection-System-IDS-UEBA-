"""Generate confusion matrix, ROC curve, and feature heatmap for IDS and UEBA models.

This script evaluates project models against local demo datasets and saves plots to disk.
Because the workspace does not contain ground-truth attack labels for both datasets,
it uses transparent proxy labels:

- IDS labels from VPC action field: REJECT -> 1 (attack), ACCEPT -> 0 (benign)
- UEBA labels from source IP heuristic: public IPv4 -> 1 (suspicious), otherwise 0
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import warnings
from pathlib import Path
from typing import Dict, Tuple

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import auc, confusion_matrix, roc_curve


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate model diagnostics plots")
    parser.add_argument("--ids-model", default="models/ddos_model.pkl", help="Path to IDS model")
    parser.add_argument("--ueba-model", default="models/uba_model.pkl", help="Path to UEBA model")
    parser.add_argument(
        "--ids-data",
        default="demo_materials/ddos_dataset.csv",
        help="Path to IDS evaluation data (VPC flow style CSV)",
    )
    parser.add_argument(
        "--ueba-data",
        default="demo_materials/parsed_logs.csv",
        help="Path to UEBA evaluation data (CloudTrail-style CSV)",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/model_diagnostics",
        help="Directory where plots and metrics JSON are saved",
    )
    return parser.parse_args()


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def is_public_ipv4(value: object) -> int:
    try:
        ip = ipaddress.ip_address(str(value))
        return int(
            ip.version == 4
            and not ip.is_private
            and not ip.is_loopback
            and not ip.is_reserved
            and not ip.is_link_local
        )
    except ValueError:
        return 0


def build_ids_dataset(csv_path: Path) -> Tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(csv_path)

    required_cols = {"col_8", "col_9", "col_10", "col_13"}
    missing = required_cols.difference(df.columns)
    if missing:
        raise ValueError(f"IDS dataset missing required columns: {sorted(missing)}")

    packets = pd.to_numeric(df["col_9"], errors="coerce").fillna(0.0)
    bytes_ = pd.to_numeric(df["col_10"], errors="coerce").fillna(0.0)
    protocol = pd.to_numeric(df["col_8"], errors="coerce").fillna(0).astype(int)

    features = pd.DataFrame(
        {
            "packets": packets,
            "bytes": bytes_,
            "byte_per_packet": np.where(packets > 0, bytes_ / packets, 0.0),
            "is_tcp": (protocol == 6).astype(int),
            "is_udp": (protocol == 17).astype(int),
            "is_icmp": (protocol == 1).astype(int),
        }
    )

    # Proxy label from VPC flow action field.
    labels = (df["col_13"].astype(str).str.upper() == "REJECT").astype(int)
    return features, labels


def build_ueba_dataset(csv_path: Path) -> Tuple[pd.DataFrame, pd.Series]:
    df = pd.read_csv(csv_path)

    required_cols = {"user", "source_ip", "time", "event", "service"}
    missing = required_cols.difference(df.columns)
    if missing:
        raise ValueError(f"UEBA dataset missing required columns: {sorted(missing)}")

    # Fill missing user IDs so group-level features stay meaningful.
    df["user"] = df["user"].fillna("").replace("", np.nan)
    df["user"] = df["user"].fillna(df["source_ip"])

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df["hour"] = df["time"].dt.hour.fillna(0)
    df["day"] = df["time"].dt.dayofweek.fillna(0)
    df["activity_volume"] = df.groupby("user")["event"].transform("count")
    df["service_diversity"] = df.groupby("user")["service"].transform("nunique")

    features = df[["hour", "day", "activity_volume", "service_diversity"]].fillna(0)

    # Proxy label: public IPv4 source is treated as suspicious.
    labels = df["source_ip"].apply(is_public_ipv4).astype(int)
    return features, labels


def model_scores_and_predictions(model, features: pd.DataFrame, anomaly_model: bool) -> Tuple[np.ndarray, np.ndarray]:
    if anomaly_model:
        decision_values = model.decision_function(features)
        # Higher decision_function means more normal; invert for attack score.
        score = (decision_values.max() - decision_values) / (
            (decision_values.max() - decision_values.min()) + 1e-9
        )
        prediction = (model.predict(features) == -1).astype(int)
        return score, prediction

    score = model.predict_proba(features)[:, 1]
    prediction = model.predict(features).astype(int)
    return score, prediction


def save_confusion_matrix(cm: np.ndarray, labels: Tuple[str, str], title: str, out_path: Path) -> None:
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=list(labels),
        yticklabels=list(labels),
    )
    plt.title(title)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def save_roc_curve(fpr: np.ndarray, tpr: np.ndarray, roc_auc: float, title: str, out_path: Path) -> None:
    plt.figure(figsize=(6, 5))
    plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.3f}", linewidth=2)
    plt.plot([0, 1], [0, 1], linestyle="--", linewidth=1)
    plt.title(title)
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend(loc="lower right")
    plt.grid(alpha=0.2)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def save_feature_heatmap(features: pd.DataFrame, title: str, out_path: Path) -> None:
    corr = features.corr(numeric_only=True)
    plt.figure(figsize=(8, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(out_path, dpi=180)
    plt.close()


def evaluate_model(
    model_name: str,
    model,
    features: pd.DataFrame,
    labels: pd.Series,
    output_dir: Path,
    anomaly_model: bool,
    label_note: str,
) -> Dict[str, object]:
    scores, predictions = model_scores_and_predictions(model, features, anomaly_model=anomaly_model)

    cm = confusion_matrix(labels, predictions)
    fpr, tpr, _ = roc_curve(labels, scores)
    roc_auc = float(auc(fpr, tpr))

    save_confusion_matrix(
        cm,
        labels=("Benign (0)", "Attack (1)"),
        title=f"{model_name} Confusion Matrix",
        out_path=output_dir / f"{model_name.lower()}_confusion_matrix.png",
    )
    save_roc_curve(
        fpr,
        tpr,
        roc_auc,
        title=f"{model_name} ROC Curve",
        out_path=output_dir / f"{model_name.lower()}_roc_curve.png",
    )
    save_feature_heatmap(
        features,
        title=f"{model_name} Feature Correlation Heatmap",
        out_path=output_dir / f"{model_name.lower()}_feature_heatmap.png",
    )

    tn, fp, fn, tp = cm.ravel().tolist()
    return {
        "samples": int(len(features)),
        "positives": int(labels.sum()),
        "negatives": int((1 - labels).sum()),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "auc": roc_auc,
        "label_definition": label_note,
    }


def main() -> None:
    args = parse_args()

    output_dir = Path(args.output_dir)
    ensure_output_dir(output_dir)

    # Reduce noise from sklearn model-version warnings during artifact generation.
    warnings.filterwarnings("ignore", message="Trying to unpickle estimator")

    ids_model = joblib.load(args.ids_model)
    ueba_model = joblib.load(args.ueba_model)

    ids_features, ids_labels = build_ids_dataset(Path(args.ids_data))
    ueba_features, ueba_labels = build_ueba_dataset(Path(args.ueba_data))

    metrics: Dict[str, object] = {}

    metrics["ids"] = evaluate_model(
        model_name="IDS",
        model=ids_model,
        features=ids_features,
        labels=ids_labels,
        output_dir=output_dir,
        anomaly_model=False,
        label_note="From demo_materials/ddos_dataset.csv: REJECT=1, ACCEPT=0",
    )

    metrics["ueba"] = evaluate_model(
        model_name="UEBA",
        model=ueba_model,
        features=ueba_features,
        labels=ueba_labels,
        output_dir=output_dir,
        anomaly_model=True,
        label_note="From demo_materials/parsed_logs.csv heuristic: public IPv4 source_ip=1, else 0",
    )

    metrics_path = output_dir / "metrics_summary.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print("Diagnostics generated:")
    print(f"  - {output_dir / 'ids_confusion_matrix.png'}")
    print(f"  - {output_dir / 'ids_roc_curve.png'}")
    print(f"  - {output_dir / 'ids_feature_heatmap.png'}")
    print(f"  - {output_dir / 'ueba_confusion_matrix.png'}")
    print(f"  - {output_dir / 'ueba_roc_curve.png'}")
    print(f"  - {output_dir / 'ueba_feature_heatmap.png'}")
    print(f"  - {metrics_path}")


if __name__ == "__main__":
    main()
