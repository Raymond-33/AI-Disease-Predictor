import json

filepath = r'C:\Users\raymo\Downloads\AI-Disease_Predictor\data\medical_knowledge.json'
with open(filepath, 'r') as f:
    data = json.load(f)

new_diseases = [
    {
      'name': 'Typhoid',
      'category': 'Infectious Disease',
      'symptoms': ['prolonged fever', 'headache', 'nausea', 'abdominal pain', 'constipation', 'diarrhea', 'fatigue', 'weakness', 'loss of appetite', 'rash', 'rose spots'],
      'description': 'Typhoid fever is a life-threatening illness caused by the bacterium Salmonella Typhi. It is typically transmitted through contaminated food or water.',
      'diagnosis': 'Diagnosed through blood, stool, or urine cultures. Widal test may also be used.',
      'severity': 'moderate-to-severe',
      'treatment': 'Antibiotics (like ciprofloxacin, azithromycin), hydration, and rest.',
      'when_to_see_doctor': 'If you experience prolonged fever and gastrointestinal symptoms.'
    },
    {
      'name': 'Hepatitis A',
      'category': 'Gastrointestinal/Liver',
      'symptoms': ['fatigue', 'sudden nausea', 'vomiting', 'abdominal pain', 'clay-colored stool', 'loss of appetite', 'low grade fever', 'dark urine', 'joint pain', 'yellowing of skin', 'jaundice'],
      'description': 'Hepatitis A is a highly contagious liver infection caused by the hepatitis A virus. It is usually transmitted through the fecal-oral route.',
      'diagnosis': 'Diagnosed via blood test detecting HAV-specific IgM antibodies.',
      'severity': 'mild-to-moderate',
      'treatment': 'No specific treatment. Rest, adequate nutrition, and fluids. It usually resolves on its own.',
      'when_to_see_doctor': 'If you notice yellowing of skin or eyes, or severe abdominal pain.'
    },
    {
      'name': 'Hepatitis B',
      'category': 'Infectious Disease/Liver',
      'symptoms': ['abdominal pain', 'dark urine', 'fever', 'joint pain', 'loss of appetite', 'nausea', 'vomiting', 'weakness', 'fatigue', 'yellowing of skin', 'jaundice'],
      'description': 'Hepatitis B is a serious liver infection caused by the hepatitis B virus (HBV). It can become chronic and increases the risk of liver failure, cancer, or cirrhosis.',
      'diagnosis': 'Diagnosed through blood tests (HBsAg, anti-HBs, anti-HBc).',
      'severity': 'variable (mild to severe)',
      'treatment': 'Antiviral medications for chronic cases. Rest and nutrition for acute infections. Vaccination is preventive.',
      'when_to_see_doctor': 'If you suspect exposure to Hepatitis B or experience persistent jaundice and fatigue.'
    },
    {
      'name': 'Fungal Infection',
      'category': 'Dermatological',
      'symptoms': ['skin redness', 'itching', 'burning skin', 'blisters', 'peeling skin', 'cracked skin', 'scaly patches'],
      'description': 'Fungal infections of the skin are common and include ringworm, athlete\'s foot, and yeast infections. They are caused by fungi that thrive in warm, moist environments.',
      'diagnosis': 'Diagnosed typically through visual inspection. Skin scraping and fungal culture can confirm.',
      'severity': 'mild',
      'treatment': 'Antifungal creams, ointments, or oral medications depending on severity.',
      'when_to_see_doctor': 'If the infection is widespread, painful, or doesn\'t improve with over-the-counter treatments.'
    },
    {
      'name': 'Allergy',
      'category': 'Immunological',
      'symptoms': ['sneezing', 'runny nose', 'itchy eyes', 'watery eyes', 'red eyes', 'skin rash', 'hives', 'swelling', 'wheezing', 'shortness of breath'],
      'description': 'An allergy occurs when the immune system reacts abnormally to a foreign substance (allergen) such as pollen, venom, or pet dander.',
      'diagnosis': 'Diagnosed through skin prick tests or blood tests (IgE).',
      'severity': 'variable (mild to severe)',
      'treatment': 'Antihistamines, decongestants, corticosteroids, and avoidance of allergens. Epinephrine for severe reactions (anaphylaxis).',
      'when_to_see_doctor': 'If you experience severe allergic reactions, swelling of the face or throat, or difficulty breathing.'
    },
    {
      'name': 'Hypotension (Low Blood Pressure)',
      'category': 'Cardiovascular',
      'symptoms': ['dizziness', 'lightheadedness', 'fainting', 'blurred vision', 'nausea', 'fatigue', 'lack of concentration', 'cold skin', 'pale skin'],
      'description': 'Hypotension is low blood pressure (typically below 90/60 mm Hg). It can cause inadequate blood flow to the brain and other vital organs.',
      'diagnosis': 'Diagnosed through blood pressure measurement. Further tests may check underlying causes (heart issues, endocrine problems).',
      'severity': 'mild-to-moderate',
      'treatment': 'Depends on cause. Increased salt intake, more fluids, wearing compression stockings, and sometimes medications.',
      'when_to_see_doctor': 'If you frequently feel dizzy or faint.'
    },
    {
      'name': 'Food Poisoning',
      'category': 'Gastrointestinal',
      'symptoms': ['nausea', 'vomiting', 'diarrhea', 'stomach cramps', 'abdominal pain', 'fever', 'weakness', 'headache', 'loss of appetite'],
      'description': 'Food poisoning is an illness caused by eating contaminated food. Common causes include bacteria (like Salmonella, E. coli), viruses, and parasites.',
      'diagnosis': 'Clinical diagnosis based on symptoms and food history. Stool tests may be done in severe cases.',
      'severity': 'mild-to-moderate',
      'treatment': 'Hydration, rest. Antidiarrheal medications (use with caution). Antibiotics only for specific bacterial infections.',
      'when_to_see_doctor': 'If symptoms persist >3 days, bloody diarrhea, or signs of severe dehydration.'
    },
    {
      'name': 'Cataracts',
      'category': 'Ophthalmological',
      'symptoms': ['cloudy vision', 'blurred vision', 'difficulty seeing at night', 'sensitivity to light', 'seeing halos around lights', 'fading colors', 'double vision in one eye'],
      'description': 'A cataract is a clouding of the normally clear lens of the eye. It develops slowly over years and eventually interferes with vision.',
      'diagnosis': 'Diagnosed through a comprehensive dilated eye exam.',
      'severity': 'chronic/serious',
      'treatment': 'Prescription glasses initially, followed by cataract surgery to replace the cloudy lens.',
      'when_to_see_doctor': 'If you experience sudden vision changes or if vision loss interferes with daily activities.'
    },
    {
      'name': 'Stomach Ulcer (Peptic Ulcer)',
      'category': 'Gastrointestinal',
      'symptoms': ['burning stomach pain', 'feeling of fullness', 'bloating', 'belching', 'intolerance to fatty foods', 'heartburn', 'nausea', 'weight loss'],
      'description': 'Stomach ulcers are painful sores in the stomach lining. They are often caused by H. pylori infection or long-term use of NSAIDs.',
      'diagnosis': 'Diagnosed via endoscopy, barium swallow, or tests for H. pylori.',
      'severity': 'moderate-to-severe',
      'treatment': 'Proton pump inhibitors (PPIs), antibiotics to clear H. pylori, and antacids.',
      'when_to_see_doctor': 'If you vomit blood, have black/tarry stools, or experience severe, sudden stomach pain.'
    },
    {
      'name': 'Mouth Ulcer (Canker Sore)',
      'category': 'Dental/Oral',
      'symptoms': ['mouth pain', 'sore inside mouth', 'painful eating', 'small white or yellow lesion', 'red border around lesion'],
      'description': 'Mouth ulcers are small, painful lesions that develop in your mouth or at the base of your gums.',
      'diagnosis': 'Clinical examination of the mouth.',
      'severity': 'mild',
      'treatment': 'Usually heal on their own in 1-2 weeks. Antimicrobial mouthwashes or topical corticosteroids can aid healing.',
      'when_to_see_doctor': 'If ulcers are unusually large, spreading, or last longer than 3 weeks.'
    }
]

data['diseases'].extend(new_diseases)

with open(filepath, 'w') as f:
    json.dump(data, f, indent=2)
print('JSON updated')
