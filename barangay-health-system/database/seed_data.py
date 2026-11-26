import random, hashlib
from datetime import date, datetime, timedelta

random.seed(8)
N = 45
PW = hashlib.sha256(b"password123").hexdigest()   # demo password for every account

FIRST = ["Maria","Jose","Juan","Ana","Mark","Jenny","Rica","Carlo","Liza","Paolo","Angel","Joy","Ramon","Grace",
         "Kevin","Mary","Joel","Nina","Ella","Dante","Cathy","Rey","Lorna","Bryan","Aira","Jerome","Mylene","Ariel",
         "Sheila","Noel","Irene","Allan","Dolly","Vic","Tess","Ben","Cora","Randy","Elena","Mario","Luz","Nestor"]
LAST  = ["Santos","Reyes","Cruz","Bautista","Garcia","Mendoza","Torres","Flores","Ramos","Aquino","Dela Cruz",
         "Navarro","Castillo","Villanueva","Domingo","Soriano","Pascual","Alvarez","Lim","Tan","Rivera","Gonzales",
         "Salazar","Fernandez","Aguilar","Manalo","Ocampo","Padilla","Valdez","Magno"]
STREETS = ["Rizal St.","Mabini St.","Bonifacio St.","Malvar St.","Burgos St.","Roxas St.","Quezon St.","Luna St."]
PUROKS  = ["Purok Maligaya","Purok Mabuhay","Purok Masagana","Purok Pag-asa","Purok Bagong Silang","Purok Sampaguita"]
POSITIONS = ["Barangay Health Worker","Midwife","Nurse","Barangay Nutrition Scholar","Health Administrator"]
REASONS = ["General check-up","Fever and cough","Blood pressure monitoring","Prenatal check-up","Child immunization",
           "Wound dressing","Diabetes monitoring","Skin rash","Headache and dizziness","Dental referral",
           "Follow-up consultation","Family planning consultation"]
DIAGNOSES = ["Acute respiratory infection","Hypertension","Type 2 diabetes","Common cold","Gastroenteritis","Dermatitis",
             "Urinary tract infection","Anemia","Mild dehydration","Allergic rhinitis","Normal prenatal visit","Migraine"]
NOTES = ["Advised rest and fluids.","Follow-up in two weeks.","Monitor blood pressure daily.","Referred to the rural health unit.",
         "Patient advised to reduce salty food.","Return if symptoms persist.","Vitals normal."]
MEDS = [("Paracetamol 500mg","Analgesic"),("Ibuprofen 200mg","Analgesic"),("Mefenamic Acid 500mg","Analgesic"),
        ("Amoxicillin 500mg","Antibiotic"),("Cotrimoxazole 400mg","Antibiotic"),("Azithromycin 500mg","Antibiotic"),
        ("Cefalexin 500mg","Antibiotic"),("Ciprofloxacin 500mg","Antibiotic"),("Amlodipine 5mg","Antihypertensive"),
        ("Losartan 50mg","Antihypertensive"),("Metoprolol 50mg","Antihypertensive"),("Metformin 500mg","Antidiabetic"),
        ("Gliclazide 80mg","Antidiabetic"),("Cetirizine 10mg","Antihistamine"),("Loratadine 10mg","Antihistamine"),
        ("Salbutamol 2mg","Bronchodilator"),("Carbocisteine 500mg","Mucolytic"),("Ambroxol 30mg","Mucolytic"),
        ("Oral Rehydration Salts","Rehydration"),("Zinc Sulfate 20mg","Supplement"),("Ferrous Sulfate 325mg","Supplement"),
        ("Vitamin C 500mg","Vitamin"),("Vitamin B Complex","Vitamin"),("Folic Acid 5mg","Vitamin"),
        ("Multivitamins Syrup","Vitamin"),("Omeprazole 20mg","Antacid"),("Aluminum Hydroxide Suspension","Antacid"),
        ("Loperamide 2mg","Antidiarrheal"),("Hyoscine 10mg","Antispasmodic"),("Mebendazole 500mg","Anthelmintic"),
        ("Albendazole 400mg","Anthelmintic"),("Povidone-Iodine Solution","Antiseptic"),("Hydrocortisone Cream","Topical"),
        ("Clotrimazole Cream","Topical"),("Mupirocin Ointment","Topical"),("Calamine Lotion","Topical"),
        ("Simvastatin 20mg","Lipid-lowering"),("Atorvastatin 20mg","Lipid-lowering"),("Prednisone 10mg","Corticosteroid"),
        ("Dexamethasone 4mg","Corticosteroid"),("Ranitidine 150mg","Antacid"),("Domperidone 10mg","Antiemetic"),
        ("Cough Syrup (Dextromethorphan)","Antitussive"),("Nystatin Drops","Antifungal"),("Fluconazole 150mg","Antifungal")]
PROGRAMS = ["Free Blood Pressure Screening","Child Immunization Drive","Prenatal Care Class","Dengue Awareness Campaign",
    "Deworming Day","Vitamin A Distribution","Senior Citizen Wellness Check","Diabetes Awareness Seminar",
    "Family Planning Seminar","Breastfeeding Awareness","Nutrition Month Feeding","Oral Health Program",
    "Mental Health Awareness Talk","Anti-Rabies Vaccination","Hypertension Support Group","Teen Health Education",
    "Mobile Blood Chemistry","Handwashing Campaign","Tuberculosis Screening","COVID-19 Booster Drive",
    "Newborn Screening Info Session","Healthy Cooking Demo","Zumba for Wellness","Smoking Cessation Class",
    "First Aid Training","Barangay Clean-up for Health","Dental Check-up Day","Eye Screening Day",
    "Malnutrition Monitoring","Herbal Medicine Workshop","Safe Water Awareness","Hepatitis B Vaccination",
    "Postpartum Care Class","Elderly Fall Prevention","Mosquito Control Drive","School Health Visit",
    "Weight Monitoring Day","Cholesterol Screening","Pregnancy Wellness Walk","Flu Vaccination Drive",
    "Healthy Heart Day","Community Fun Run","Infant Care Workshop","Proper Medication Use Talk","Sanitation Campaign"]
ANN = ["Free Check-up this Friday","Health Center Schedule Update","Medicine Stock Update","Vaccination Schedule",
       "Dengue Prevention Reminder","Holiday Clinic Hours","New Health Worker Assigned","Program Registration Open",
       "Reminder: Bring Your ID","Blood Pressure Screening Results Day","Deworming for School Children","Prenatal Class Schedule",
       "Cancelled Activity Notice","Clean Water Advisory","Flu Season Tips","Senior Citizens Wellness Day",
       "Medical Mission Announcement","Nutrition Month Activities","Health Center Cleaning Day","Updated Appointment Rules",
       "Free Dental Check-up","Mobile Clinic Visit","Anti-Rabies Vaccination Day","Health Card Reminder",
       "Emergency Contact Numbers","Registration for Zumba","Diabetes Seminar Invitation","Hygiene Kit Distribution",
       "Rainy Season Health Tips","Mother and Baby Care Day","Heat Safety Advisory","COVID-19 Booster Schedule",
       "Lost and Found Health Cards","Volunteer Call","Medicine Request Process","Late Appointment Policy",
       "Tuberculosis Screening Day","Healthy Cooking Demo Invite","Eye Check-up Schedule","Sanitation Drive Notice",
       "Weighing Day Reminder","First Aid Training Invite","Health Survey Participation","Year-End Clinic Schedule","New Online Appointment Feature"]

def q(v):
    if v is None: return "NULL"
    if isinstance(v,(int,float)): return str(v)
    return "'" + str(v).replace("\\","\\\\").replace("'","''") + "'"

def phone(used):
    while True:
        p = "09" + "".join(random.choice("0123456789") for _ in range(9))
        if p not in used:
            used.add(p); return p

def names(n):
    seen=set(); out=[]
    while len(out)<n:
        nm=f"{random.choice(FIRST)} {random.choice(LAST)}"
        if nm not in seen: seen.add(nm); out.append(nm)
    return out

def insert(table, cols, rows):
    s=f"INSERT INTO {table} ({', '.join(cols)}) VALUES\n"
    s+=",\n".join("  ("+", ".join(q(v) for v in r)+")" for r in rows)+";\n\n"
    return s

used=set(); out=["USE barangay_health_system;\n\n"]
today=date.today()

# Residents
rn=names(N); rows=[]
for i,nm in enumerate(rn,1):
    bd=today-timedelta(days=random.randint(365,365*85))
    created=datetime.now()-timedelta(days=random.randint(1,400))
    rows.append((nm,bd,phone(used),f"{random.choice(PUROKS)}, {random.choice(STREETS)}, Puerto Princesa City",
                 created.strftime("%Y-%m-%d %H:%M:%S"),f"resident{i:02d}",PW))
out.append(insert("Residents",["full_name","birth_date","contact_number","address","created_at","username","password_hash"],rows))

# Health workers (last 4 are Inactive)
wn=names(N); rows=[]
for i,nm in enumerate(wn,1):
    rows.append((nm,random.choice(POSITIONS),phone(used),"Inactive" if i>N-4 else "Active",f"worker{i:02d}",PW))
out.append(insert("Health_Workers",["full_name","position","contact_number","status","username","password_hash"],rows))
ACTIVE=list(range(1,N-3))

# Appointments
rows=[]; taken=set(); times=[(8,0),(9,0),(10,0),(11,0),(13,0),(14,0),(15,0)]
while len(rows)<N:
    w=random.choice(ACTIVE); d=today+timedelta(days=random.randint(-60,30)); h,m=random.choice(times)
    if (w,d,h) in taken: continue
    taken.add((w,d,h))
    if d<today: st=random.choice(["Completed","Completed","Cancelled","Rejected"])
    else: st=random.choice(["Pending","Pending","Approved","Cancelled"])
    rows.append((d,f"{h:02d}:{m:02d}:00",f"{h:02d}:30:00",random.choice(REASONS),st,random.randint(1,N),w))
out.append(insert("Appointments",["appointment_date","start_time","end_time","reason","status","resident_id","worker_id"],rows))

# Medical records
rows=[]; rec_res={}
for i in range(1,N+1):
    r=random.randint(1,N); rec_res[i]=r
    rows.append((today-timedelta(days=random.randint(1,200)),random.choice(DIAGNOSES),random.choice(NOTES),r,random.choice(ACTIVE)))
out.append(insert("Medical_Records",["visit_date","diagnosis","notes","resident_id","worker_id"],rows))

# Medicines (status set by trigger)
rows=[]; qty={}
for i,(nm,cat) in enumerate(MEDS,1):
    qv=random.choice([0,5,12,18,30,50,80,120,200]) if i%9 else random.choice([50,80,120])
    if i in (1,2,4,9,12): qv=max(qv,80)       # popular medicines always in stock
    qty[i]=qv
    rows.append((nm,cat,qv,"Available"))
out.append(insert("Medicines",["medicine_name","category","quantity","availability_status"],rows))

# Prescriptions
instr=["Take 1 tablet every 6 hours after meals.","Take 1 tablet twice a day for 7 days.","Take 1 tablet once daily in the morning.",
       "Apply thin layer twice daily.","Take as needed for pain, not more than 4 times a day.","Take 1 tablet at bedtime."]
stocked=[m for m,v in qty.items() if v>=5]; rows=[]
for i in range(1,N+1):
    rec=i
    rows.append((random.randint(1,5),random.choice(instr),
                 (datetime.now()-timedelta(days=random.randint(1,150))).strftime("%Y-%m-%d %H:%M:%S"),
                 rec_res[rec],random.choice(ACTIVE),random.choice(stocked),rec))
out.append(insert("Prescriptions",["quantity","instructions","prescribed_at","resident_id","worker_id","medicine_id","record_id"],rows))

# Health programs
rows=[]
for i,nm in enumerate(PROGRAMS,1):
    d=datetime.now()+timedelta(days=random.randint(-90,90),hours=random.randint(-5,5))
    d=d.replace(hour=random.choice([8,9,13,14]),minute=0,second=0,microsecond=0)
    st="Completed" if d.date()<today else random.choice(["Upcoming","Upcoming","Cancelled"])
    rows.append((nm,f"Barangay health activity: {nm}.",d.strftime("%Y-%m-%d %H:%M:%S"),st,random.choice(ACTIVE)))
out.append(insert("Health_Programs",["program_name","description","schedule","status","worker_id"],rows))

# Program registrations (unique resident/program pairs)
pairs=set()
while len(pairs)<N: pairs.add((random.randint(1,N),random.randint(1,N)))
rows=[]
for r,p in sorted(pairs):
    rows.append(((datetime.now()-timedelta(days=random.randint(1,100))).strftime("%Y-%m-%d %H:%M:%S"),
                 random.choice(["Registered","Registered","Attended","Cancelled"]),r,p))
out.append(insert("Program_Registrations",["registered_at","status","resident_id","program_id"],rows))

# Announcements
rows=[]
for t in ANN:
    rows.append((t,f"{t}. Please visit the barangay health center for more details.",
                 (datetime.now()-timedelta(days=random.randint(0,120))).strftime("%Y-%m-%d %H:%M:%S"),random.choice(ACTIVE)))
out.append(insert("Announcements",["title","content","date_posted","worker_id"],rows))

with open("02_seed_data.sql","w",encoding="utf-8") as f: f.write("".join(out))
print("Created 02_seed_data.sql")
