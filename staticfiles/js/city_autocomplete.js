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
            "Istanbul", "Cape Town", "Rio de Janeiro", "Buenos Aires", "Mexico City", "Baku"
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
      const value = input.value.toLowerCase();
      suggestionsBox.innerHTML = '';
      if (value.length < 2) {
        suggestionsBox.style.display = 'none';
        return;
      }
  
      const matches = cities.filter(city => city.toLowerCase().startsWith(value));
      if (matches.length === 0) {
        suggestionsBox.style.display = 'none';
        return;
      }
  
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
  
      const rect = input.getBoundingClientRect();
      suggestionsBox.style.top = rect.bottom + window.scrollY + "px";
      suggestionsBox.style.left = rect.left + window.scrollX + "px";
      suggestionsBox.style.width = rect.width + "px";
      suggestionsBox.style.display = 'block';
    });
  
    document.addEventListener('click', (e) => {
      if (!suggestionsBox.contains(e.target) && e.target !== input) {
        suggestionsBox.style.display = 'none';
      }
    });
  });
  