"""The full state-wise city list supplied by the user.

This is the source of truth for the expanded registry. `build_cities.py`
matches each name against the SimpleMaps world-cities dataset to obtain real
coordinates and populations, and writes `data/cities_full.csv`.
"""

INDIA_CITIES_FULL = {
    "Maharashtra": [
        "Mumbai", "Pune", "Nagpur", "Nashik", "Thane", "Navi Mumbai",
        "Chhatrapati Sambhajinagar", "Solapur", "Kolhapur", "Amravati", "Nanded",
        "Sangli", "Jalgaon", "Akola", "Latur", "Dhule", "Ahilyanagar", "Chandrapur",
        "Parbhani", "Ichalkaranji", "Malegaon", "Jalna", "Beed", "Wardha",
        "Yavatmal", "Ratnagiri", "Satara", "Baramati", "Panvel", "Mira-Bhayandar",
        "Vasai-Virar", "Kalyan-Dombivli", "Ulhasnagar", "Ambarnath", "Bhiwandi",
        "Dharashiv", "Gondia", "Bhusawal", "Hingoli", "Washim",
    ],
    "Gujarat": [
        "Ahmedabad", "Surat", "Vadodara", "Rajkot", "Gandhinagar", "Bhavnagar",
        "Jamnagar", "Junagadh", "Anand", "Nadiad", "Morbi", "Mehsana", "Bharuch",
        "Vapi", "Navsari", "Porbandar", "Palanpur", "Godhra", "Veraval",
        "Gandhidham", "Bhuj", "Surendranagar", "Amreli", "Botad", "Dahod",
        "Patan", "Valsad", "Kalol", "Deesa", "Jetpur",
    ],
    "Madhya Pradesh": [
        "Indore", "Bhopal", "Jabalpur", "Gwalior", "Ujjain", "Sagar", "Dewas",
        "Satna", "Ratlam", "Rewa", "Singrauli", "Burhanpur", "Khandwa", "Morena",
        "Chhindwara", "Bhind", "Shivpuri", "Vidisha", "Guna", "Damoh", "Mandsaur",
        "Neemuch", "Itarsi", "Betul", "Sehore", "Narmadapuram", "Pithampur",
        "Dhar", "Chhatarpur", "Khargone",
    ],
    "Uttar Pradesh": [
        "Lucknow", "Kanpur", "Ghaziabad", "Agra", "Varanasi", "Prayagraj",
        "Meerut", "Noida", "Greater Noida", "Bareilly", "Aligarh", "Moradabad",
        "Saharanpur", "Gorakhpur", "Mathura", "Firozabad", "Jhansi",
        "Muzaffarnagar", "Ayodhya", "Rampur", "Shahjahanpur", "Farrukhabad",
        "Etawah", "Mirzapur", "Hapur", "Bijnor", "Amroha", "Unnao", "Rae Bareli",
        "Sitapur", "Lakhimpur", "Banda", "Gonda", "Deoria", "Azamgarh", "Ballia",
        "Jaunpur", "Basti", "Sambhal", "Orai",
    ],
    "Rajasthan": [
        "Jaipur", "Jodhpur", "Kota", "Udaipur", "Ajmer", "Bikaner", "Alwar",
        "Bharatpur", "Bhilwara", "Sikar", "Sri Ganganagar", "Pali", "Tonk",
        "Kishangarh", "Beawar", "Chittorgarh", "Barmer", "Jaisalmer", "Dholpur",
        "Hanumangarh",
    ],
    "Delhi": [
        "New Delhi", "Delhi", "Dwarka", "Rohini", "Narela", "Karol Bagh",
        "Shahdara", "Najafgarh", "Saket", "Vasant Kunj",
    ],
    "Karnataka": [
        "Bengaluru", "Mysuru", "Hubballi-Dharwad", "Mangaluru", "Belagavi",
        "Kalaburagi", "Davanagere", "Ballari", "Vijayapura", "Shivamogga",
        "Tumakuru", "Udupi", "Hassan", "Raichur", "Bidar", "Hosapete",
        "Chitradurga", "Gadag", "Kolar", "Mandya", "Chikkamagaluru", "Karwar",
        "Ramanagara", "Bagalkot", "Yadgir",
    ],
    "Tamil Nadu": [
        "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
        "Tiruppur", "Erode", "Tirunelveli", "Vellore", "Thoothukudi", "Dindigul",
        "Thanjavur", "Ranipet", "Nagercoil", "Kanchipuram", "Karur", "Hosur",
        "Cuddalore", "Sivakasi", "Namakkal", "Tiruvannamalai", "Pollachi",
        "Pudukkottai", "Krishnagiri", "Nagapattinam",
    ],
    "Telangana": [
        "Hyderabad", "Warangal", "Karimnagar", "Nizamabad", "Khammam",
        "Ramagundam", "Mahbubnagar", "Nalgonda", "Adilabad", "Siddipet",
        "Suryapet", "Miryalaguda", "Mancherial", "Jagtial", "Kothagudem",
        "Sangareddy", "Medak", "Vikarabad", "Bodhan", "Wanaparthy",
    ],
    "Andhra Pradesh": [
        "Visakhapatnam", "Vijayawada", "Guntur", "Nellore", "Kurnool", "Tirupati",
        "Rajamahendravaram", "Kakinada", "Kadapa", "Anantapur", "Eluru", "Ongole",
        "Machilipatnam", "Srikakulam", "Vizianagaram", "Chittoor", "Tenali",
        "Proddatur", "Hindupur", "Amaravati",
    ],
    "Kerala": [
        "Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kollam", "Kannur",
        "Alappuzha", "Palakkad", "Kottayam", "Malappuram", "Manjeri", "Thalassery",
        "Ponnani", "Kasaragod", "Pathanamthitta", "Vatakara", "Perinthalmanna",
        "Kanhangad", "Guruvayur", "Idukki",
    ],
    "West Bengal": [
        "Kolkata", "Howrah", "Durgapur", "Asansol", "Siliguri", "Bardhaman",
        "Kharagpur", "Haldia", "Darjeeling", "Malda", "Jalpaiguri", "Baharampur",
        "Krishnanagar", "Raiganj", "Cooch Behar", "Alipurduar", "Bankura",
        "Purulia", "Ranaghat", "Chandannagar",
    ],
    "Bihar": [
        "Patna", "Gaya", "Bhagalpur", "Muzaffarpur", "Darbhanga", "Purnia",
        "Bihar Sharif", "Arrah", "Begusarai", "Katihar", "Munger", "Chhapra",
        "Bettiah", "Samastipur", "Hajipur", "Sasaram", "Dehri", "Motihari",
        "Kishanganj", "Sitamarhi",
    ],
    "Jharkhand": [
        "Ranchi", "Jamshedpur", "Dhanbad", "Bokaro Steel City", "Deoghar",
        "Hazaribagh", "Giridih", "Ramgarh", "Medininagar", "Phusro", "Chaibasa",
        "Dumka", "Sahibganj", "Godda", "Gumla", "Lohardaga", "Chatra", "Koderma",
        "Jamtara", "Simdega",
    ],
    "Odisha": [
        "Bhubaneswar", "Cuttack", "Rourkela", "Berhampur", "Sambalpur", "Puri",
        "Balasore", "Baripada", "Bhadrak", "Jharsuguda", "Jeypore", "Angul",
        "Dhenkanal", "Kendujhar", "Rayagada", "Koraput", "Paradip", "Bargarh",
        "Sundargarh", "Talcher",
    ],
    "Chhattisgarh": [
        "Raipur", "Bhilai", "Bilaspur", "Korba", "Durg", "Rajnandgaon",
        "Jagdalpur", "Raigarh", "Ambikapur", "Dhamtari", "Mahasamund", "Chirmiri",
        "Kawardha", "Kanker", "Dantewada", "Janjgir", "Mungeli", "Balod",
        "Bemetara", "Tilda Newra",
    ],
    "Punjab": [
        "Ludhiana", "Amritsar", "Jalandhar", "Patiala", "Bathinda", "Mohali",
        "Hoshiarpur", "Pathankot", "Moga", "Batala", "Khanna", "Phagwara",
        "Abohar", "Malerkotla", "Barnala", "Firozpur", "Kapurthala", "Faridkot",
        "Sangrur", "Muktsar",
    ],
    "Haryana": [
        "Faridabad", "Gurugram", "Panipat", "Ambala", "Yamunanagar", "Rohtak",
        "Hisar", "Karnal", "Sonipat", "Panchkula", "Bhiwani", "Sirsa",
        "Bahadurgarh", "Jind", "Rewari", "Kaithal", "Palwal", "Kurukshetra",
        "Fatehabad", "Narnaul",
    ],
    "Uttarakhand": [
        "Dehradun", "Haridwar", "Roorkee", "Haldwani", "Rudrapur", "Kashipur",
        "Rishikesh", "Nainital", "Almora", "Pithoragarh", "Kotdwar", "Vikasnagar",
        "Mussoorie", "Ramnagar", "Srinagar", "Tehri", "Chamoli", "Uttarkashi",
    ],
    "Himachal Pradesh": [
        "Shimla", "Dharamshala", "Solan", "Mandi", "Baddi", "Kullu", "Manali",
        "Una", "Hamirpur", "Bilaspur", "Chamba", "Nahan", "Paonta Sahib",
        "Sundernagar", "Palampur",
    ],
    "Assam": [
        "Guwahati", "Silchar", "Dibrugarh", "Jorhat", "Tinsukia", "Tezpur",
        "Nagaon", "Bongaigaon", "Diphu", "Sivasagar", "Goalpara",
        "North Lakhimpur", "Barpeta", "Karimganj", "Dhemaji", "Haflong",
    ],
    "Arunachal Pradesh": [
        "Itanagar", "Naharlagun", "Pasighat", "Tawang", "Ziro", "Bomdila", "Aalo",
        "Tezu", "Roing", "Namsai",
    ],
    "Meghalaya": [
        "Shillong", "Tura", "Jowai", "Nongstoin", "Williamnagar", "Baghmara",
        "Resubelpara", "Khliehriat", "Mairang",
    ],
    "Manipur": [
        "Imphal", "Thoubal", "Bishnupur", "Churachandpur", "Kakching", "Ukhrul",
        "Senapati", "Tamenglong", "Moreh", "Jiribam",
    ],
    "Mizoram": [
        "Aizawl", "Lunglei", "Champhai", "Serchhip", "Kolasib", "Saiha",
        "Lawngtlai", "Mamit", "Saitual", "Khawzawl",
    ],
    "Nagaland": [
        "Dimapur", "Kohima", "Mokokchung", "Tuensang", "Wokha", "Zunheboto",
        "Mon", "Phek", "Kiphire", "Longleng",
    ],
    "Tripura": [
        "Agartala", "Udaipur", "Dharmanagar", "Kailashahar", "Belonia", "Ambassa",
        "Khowai", "Teliamura", "Bishalgarh", "Sabroom",
    ],
    "Sikkim": [
        "Gangtok", "Namchi", "Gyalshing", "Mangan", "Singtam", "Rangpo",
        "Jorethang", "Pakyong",
    ],
    "Jammu and Kashmir": [
        "Srinagar", "Jammu", "Anantnag", "Baramulla", "Udhampur", "Kathua",
        "Sopore", "Pulwama", "Rajouri", "Poonch", "Doda", "Kupwara", "Bandipora",
        "Kishtwar", "Samba", "Bijbehara",
    ],
    "Ladakh": ["Leh", "Kargil", "Diskit", "Padum", "Nyoma"],
    "Goa": [
        "Panaji", "Margao", "Vasco da Gama", "Mapusa", "Ponda", "Bicholim",
        "Curchorem", "Canacona", "Sanquelim", "Cuncolim",
    ],
    "Chandigarh": ["Chandigarh"],
    "Puducherry": ["Puducherry", "Karaikal", "Mahe", "Yanam"],
    "Andaman and Nicobar Islands": [
        "Sri Vijaya Puram", "Diglipur", "Mayabunder", "Rangat", "Car Nicobar",
    ],
    "Dadra and Nagar Haveli and Daman and Diu": ["Silvassa", "Daman", "Diu"],
    "Lakshadweep": ["Kavaratti", "Agatti", "Andrott", "Minicoy"],
}
