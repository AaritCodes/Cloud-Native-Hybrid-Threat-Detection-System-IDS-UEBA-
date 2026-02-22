from ids_engine import IDSEngine
from ueba_engine import UEBAEngine
from threat_fusion_engine import combine_risks
import time
import warnings

warnings.filterwarnings("ignore")

ids = IDSEngine("models/ddos_model.pkl")
ueba = UEBAEngine("models/uba_model.pkl")

while True:

    print("\n===== Hybrid Threat Detection Cycle =====")

    print("Running IDS...")
    network_results = ids.detect()
    print("IDS Done")

    print("Running UEBA...")
    user_results = ueba.detect()
    print("UEBA Done")

    print("Network Results:", network_results)
    print("User Results:", user_results)

    for net in network_results:
        ip = net["ip"]
        network_risk = net["network_risk"]

        matched_user = next(
            (u for u in user_results if u["ip"] == ip),
            None
        )

        user_risk = matched_user["user_risk"] if matched_user else 0.1

        final_risk, level = combine_risks(network_risk, user_risk)

        print(f"""
IP: {ip}
Network Risk: {network_risk:.2f}
User Risk: {user_risk:.2f}
Final Risk: {final_risk:.2f}
Threat Level: {level}
""")

    time.sleep(10)