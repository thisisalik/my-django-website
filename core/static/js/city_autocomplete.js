document.addEventListener('DOMContentLoaded', function () {
  const cities = [
    // Germany
    "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt", "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen", "Bremen", "Dresden", "Hanover", "Nuremberg", "Freiburg",
    // France
    "Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Strasbourg", "Montpellier", "Bordeaux", "Lille", "Rennes", "Reims", "Le Havre", "Saint-Étienne", "Grenoble",
    // Spain
    "Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza", "Málaga", "Murcia", "Palma", "Bilbao", "Alicante", "Cordoba", "Valladolid",
    // Italy
    "Rome", "Milan", "Naples", "Turin", "Palermo", "Genoa", "Bologna", "Florence", "Bari", "Catania", "Venice", "Verona",
    // Poland
    "Warsaw", "Krakow", "Lodz", "Wroclaw", "Poznan", "Gdansk", "Szczecin", "Lublin", "Bydgoszcz", "Katowice",
    // Netherlands
    "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven", "Tilburg", "Groningen", "Breda",
    // Sweden
    "Stockholm", "Gothenburg", "Malmö", "Uppsala", "Västerås", "Örebro", "Linköping",
    // Belgium
    "Brussels", "Antwerp", "Ghent", "Charleroi", "Liège", "Bruges", "Namur", "Leuven",
    // 🌎 Famous global cities
    "New York", "Los Angeles", "Chicago", "San Francisco", "Houston", "Toronto", "Vancouver",
    "Tokyo", "Seoul", "Beijing", "Shanghai", "Sydney", "Melbourne", "Bangkok", "Singapore", "Dubai",
    "Istanbul", "Cape Town", ,
    "Miami", "Rio de Janeiro", "Buenos Aires", "Mexico City", "Baku", 
    // Albania
"Dijon","Angers","Grenoble","Metz","Rouen","Tours","Saint-Denis",
// Georgia (neighbor)
"Tbilisi","Kutaisi","Batumi",
// Germany (extras)
"Bochum","Wuppertal","Bonn","Münster","Mannheim","Karlsruhe","Augsburg","Wiesbaden","Kiel",
// Greece
"Athens","Thessaloniki","Patras","Heraklion","Larissa","Volos","Chania",
// Hungary
"Budapest","Debrecen","Szeged","Miskolc","Pécs","Győr",
// Iceland
"Reykjavik","Kópavogur","Hafnarfjörður",
// Ireland
"Dublin","Cork","Limerick","Galway","Waterford",
// Italy (extras)
"Padua","Parma","Trieste","Taranto","Brescia","Reggio Calabria","Perugia",
// Kazakhstan (western neighbor)
"Aktobe","Atyrau","Oral",
// Kosovo
"Pristina","Prizren","Peja","Gjakova",
// Latvia
"Riga","Daugavpils","Liepāja","Jelgava",
// Liechtenstein
"Vaduz","Schaan",
// Lithuania
"Vilnius","Kaunas","Klaipėda","Šiauliai","Panevėžys",
// Luxembourg
"Luxembourg","Esch-sur-Alzette",
// Malta
"Valletta","Birkirkara","Sliema","Mosta",
// Moldova
"Chișinău","Bălți","Tiraspol",
// Monaco
"Monaco","Monte Carlo",
// Montenegro
"Podgorica","Nikšić","Herceg Novi","Bar",
// Netherlands (extras)
"Nijmegen","Apeldoorn","Haarlem","Arnhem","Amersfoort",
// North Macedonia
"Skopje","Bitola","Kumanovo","Tetovo","Ohrid",
// Norway
"Oslo","Bergen","Trondheim","Stavanger","Drammen","Tromsø",
// Portugal
"Lisbon","Porto","Vila Nova de Gaia","Braga","Coimbra","Faro",
// Romania
"Bucharest","Cluj-Napoca","Timișoara","Iași","Constanța","Craiova","Brașov","Galați","Ploiești",
// Russia (European part)
"Moscow","Saint Petersburg","Nizhny Novgorod","Kazan","Samara","Rostov-on-Don","Ufa","Volgograd","Voronezh",
// San Marino
"San Marino",
// Serbia
"Belgrade","Novi Sad","Niš","Kragujevac","Subotica",
// Slovakia
"Bratislava","Košice","Prešov","Žilina","Nitra",
// Slovenia
"Ljubljana","Maribor","Celje","Koper",
// Spain (extras)
"Gijón","Vigo","A Coruña","Granada","Elche","Cartagena","Santander",
// Switzerland
"Zurich","Geneva","Basel","Lausanne","Bern","Lugano","St. Gallen",
// Turkey (straddles EU/Asia, include big ones)
"Ankara","Izmir","Bursa","Antalya","Adana","Konya","Gaziantep","Eskisehir",
// Ukraine
"Kyiv","Kharkiv","Odesa","Dnipro","Lviv","Zaporizhzhia","Mykolaiv","Mariupol",
// United Kingdom
"London","Birmingham","Manchester","Leeds","Glasgow","Liverpool","Edinburgh","Bristol","Cardiff","Belfast",
// Vatican City
"Vatican City",
// Central Asia
"Almaty","Astana","Shymkent","Tashkent","Samarkand","Bukhara","Bishkek","Osh","Dushanbe","Khujand","Ashgabat",
// East Asia — China (selection)
"Beijing","Shanghai","Shenzhen","Guangzhou","Chengdu","Chongqing","Wuhan","Hangzhou","Nanjing","Tianjin","Xi'an","Suzhou","Qingdao","Dalian",
// East Asia — Japan
"Tokyo","Yokohama","Osaka","Nagoya","Sapporo","Fukuoka","Kobe","Kyoto","Hiroshima","Sendai",
// East Asia — Korea
"Seoul","Busan","Incheon","Daegu","Daejeon","Gwangju","Ulsan",
// South Asia — India
"Delhi","Mumbai","Bengaluru","Kolkata","Chennai","Hyderabad","Pune","Ahmedabad","Jaipur","Surat","Lucknow","Kanpur","Nagpur","Indore","Bhopal","Visakhapatnam","Patna","Vadodara","Ludhiana",
// South Asia — Pakistan/Bangladesh/Sri Lanka/Nepal
"Karachi","Lahore","Islamabad","Rawalpindi","Faisalabad","Multan","Peshawar",
"Dhaka","Chittagong","Khulna","Rajshahi",
"Colombo","Kandy","Galle",
"Kathmandu","Pokhara",
// Southeast Asia
"Bangkok","Chiang Mai","Phuket","Hanoi","Ho Chi Minh City","Da Nang","Haiphong",
"Jakarta","Surabaya","Bandung","Medan","Makassar","Yogyakarta",
"Manila","Quezon City","Cebu City","Davao City",
"Kuala Lumpur","George Town","Johor Bahru","Kuching","Kota Kinabalu",
"Singapore","Vientiane","Phnom Penh","Naypyidaw","Yangon",
// West Asia / Middle East
"Istanbul","Ankara","Izmir","Bursa","Antalya",
"Tehran","Mashhad","Isfahan","Shiraz","Tabriz",
"Baghdad","Basra","Erbil","Mosul",
"Riyadh","Jeddah","Dammam","Mecca","Medina",
"Doha","Kuwait City","Manama","Abu Dhabi","Dubai","Sharjah",
"Amman","Damascus","Aleppo","Beirut","Jerusalem","Tel Aviv",
// Caucasus (also in Europe list)
"Yerevan","Tbilisi","Baku",

  ];

  const input = document.getElementById('id_location');
  if (!input) return;

  let suggestionsBox = document.createElement('div');
  suggestionsBox.id = 'city-suggestions';
  suggestionsBox.style.position = 'absolute';
  suggestionsBox.style.border = '1px solid #ccc';
  suggestionsBox.style.background = '#fff';
  suggestionsBox.style.zIndex = '1000';
  suggestionsBox.style.display = 'none';
  document.body.appendChild(suggestionsBox);

  input.addEventListener('input', () => {
    const value = input.value.toLowerCase().trim();  // ✅ Define `value` before using it
    console.log("Input changed:", value);

    suggestionsBox.innerHTML = '';
    suggestionsBox.style.display = 'none';

    if (value.length < 1) return;

    const matches = cities.filter(city =>
      city.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").includes(value)
    );

    if (matches.length === 0) return;

    matches.forEach(city => {
      const div = document.createElement('div');
      div.textContent = city;
      div.style.padding = '5px';
      div.style.cursor = 'pointer';
      div.addEventListener('click', () => {
        input.value = city;
        suggestionsBox.style.display = 'none';
      });
      suggestionsBox.appendChild(div);
    });

    // Position and show suggestions
    setTimeout(() => {
      const rect = input.getBoundingClientRect();
      suggestionsBox.style.top = `${rect.bottom + window.scrollY}px`;
      suggestionsBox.style.left = `${rect.left + window.scrollX}px`;
      suggestionsBox.style.width = `${rect.width}px`;
      suggestionsBox.style.display = 'block';
    }, 10);
  });
});
