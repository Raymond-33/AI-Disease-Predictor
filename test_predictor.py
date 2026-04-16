from predictor import predict_diseases

r = predict_diseases('I have high fever severe headache pain behind my eyes joint pain and skin rash')
for p in r.get('predictions', []):
    print(f"[{p['rank']}] {p['disease']}: {p['confidence']}%")
print('Symptoms:', r.get('symptoms_detected', [])[:5])
