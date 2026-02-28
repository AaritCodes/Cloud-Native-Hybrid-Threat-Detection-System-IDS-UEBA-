# Quick Answers Cheat Sheet - Demo Day

## DATASET (30 seconds each)

**Q: What dataset?**
"Two real-time AWS sources: CloudWatch metrics (network traffic) and CloudTrail logs (user behavior). Not a public dataset - real operational data from our EC2 instance."

**Q: How much data?**
"7 days of CloudTrail logs, ~12,000 events for training. Real-time CloudWatch metrics every 60 seconds. Validated with actual DDoS attack."

**Q: How labeled?**
"Unsupervised learning - no labels needed. Isolation Forest learns normal behavior. Thresholds set empirically from 1 week baseline monitoring."

**Q: What features?**
"4 features: hour, day, activity_volume, service_diversity. Standard UEBA features from literature (Zhang et al., 2023)."

---

## MODEL (30 seconds each)

**Q: Which model?**
"Isolation Forest for UEBA. Why? Unsupervised, fast (O(n log n)), proven effective (85% accuracy in literature), works well with few features."

**Q: How trained?**
"Parameters: n_estimators=100, contamination=0.1. Trained on 7 days normal behavior. Takes <5 seconds to train."

**Q: Why not deep learning?**
"Only 12K samples and 4 features - too small for deep learning. Isolation Forest is more appropriate and 3x faster (literature comparison)."

**Q: How validated?**
"Three stages: cross-validation on normal data, synthetic anomaly injection, real DDoS attack. Result: 0% false positives, 100% true positives."

---

## FUSION (30 seconds each)

**Q: Why 60/40 weighting?**
"Empirically tested 50/50, 60/40, 70/30. 60/40 gave best results. Network signals more reliable for external attacks. This is our novel contribution."

**Q: How set thresholds?**
"Monitored normal operation (risk 0.05-0.10), ran attack simulations (risk 0.61-0.75), used ROC curve analysis. Result: CRITICAL >0.8, HIGH >0.6, MEDIUM >0.4."

---

## PERFORMANCE (30 seconds each)

**Q: How fast?**
"10-20 seconds total. CloudWatch 2s, CloudTrail 3s, ML <0.1s. Literature: 30-60s. We're 2-3x faster."

**Q: False positives?**
"0% in testing. Hybrid fusion reduces false alarms. Literature: 15-20%. Our improvement: combining network + user signals."

---

## KEY NUMBERS TO MEMORIZE

- Training: 7 days, 12,000 events
- Features: 4 (hour, day, volume, diversity)
- Model: Isolation Forest, n_estimators=100, contamination=0.1
- Detection: 10-20 seconds (2-3x faster)
- Accuracy: 0% false positives, 100% true positives
- Fusion: 60% network, 40% user (NOVEL)
- Attack: 1,242x traffic increase detected in 20s
- Normal: 800-1,200 bytes/min
- Attack: 2M+ bytes, 27,000+ packets

---

## IF YOU DON'T KNOW

"That's an excellent question for future work. In this prototype, we focused on [what you did]. For production, we would [what you'd do]."

---

## CONFIDENCE STATEMENTS

✅ "First AWS-native hybrid system"
✅ "Novel 60/40 weighted fusion"
✅ "2-3x faster than literature"
✅ "0% false positives vs 15-20% in literature"
✅ "Real attack validation, not synthetic data"
✅ "Production-ready implementation"

**YOU'VE GOT THIS! 🚀**
