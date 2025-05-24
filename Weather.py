import os
import json
import requests
import tkinter as tk
from tkinter import ttk, messagebox, font
from datetime import datetime, timedelta
from dateutil import parser
from PIL import Image, ImageTk, ImageDraw, ImageFont
from typing import Optional

# =========================
# Constants
# =========================

API_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
API_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".weather_cache")
CACHE_EXPIRY_HOURS = 1

def get_cache_file(city: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{city.lower()}.json")

def load_cache(city: str) -> Optional[dict]:
    cache_file = get_cache_file(city)
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            timestamp = parser.parse(data["timestamp"])
            if datetime.now(timestamp.tzinfo) < timestamp + timedelta(hours=CACHE_EXPIRY_HOURS):
                return data
    except Exception as e:
        print(f"Cache error for {city}: {e}")
    return None

def save_cache(city: str, weather_data: dict) -> None:
    cache_file = get_cache_file(city)
    weather_data["timestamp"] = datetime.now().isoformat()
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(weather_data, f)
    except IOError:
        print(f"Warning: Failed to save cache for {city}")

def get_weather_desc(code: int) -> str:
    weather_descriptions = {
        0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing Rime Fog", 51: "Light Drizzle", 53: "Moderate Drizzle",
        55: "Dense Drizzle", 56: "Light Freezing Drizzle", 57: "Dense Freezing Drizzle",
        61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain", 66: "Light Freezing Rain",
        67: "Heavy Freezing Rain", 71: "Slight Snow Fall", 73: "Moderate Snow Fall",
        75: "Heavy Snow Fall", 77: "Snow Grains", 80: "Slight Rain Showers",
        81: "Moderate Rain Showers", 82: "Violent Rain Showers", 85: "Slight Snow Showers",
        86: "Heavy Snow Showers", 95: "Thunderstorm", 96: "Thunderstorm with Slight Hail",
        99: "Thunderstorm with Heavy Hail"
    }
    return weather_descriptions.get(code, "Unknown")

# =========================
# Main App Class
# =========================

class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WeatherAPP")
        self.geometry("420x350")
        self.resizable(False, False)

        # === Background with Rendered Title ===
         # === Load background image ===
        image_path = r"c:\Users\Dickens\Downloads\pexels-jplenio-1118873.jpg"
        try:
            bg_image = Image.open(image_path).resize((420, 350), Image.LANCZOS)
            draw = ImageDraw.Draw(bg_image)

            # === Draw title text on image ===
            font_path = "C:/Windows/Fonts/Segoe UI.ttf" 
            title_font = ImageFont.truetype(font_path, 24)
            text = "WeatherAPP"
            text_width, text_height = draw.textsize(text, font=title_font)
            draw.text(((420 - text_width) // 2, 15), text, font=title_font, fill="white")

            # === Display the image ===
            self.bg_photo = ImageTk.PhotoImage(bg_image)
            self.bg_label = tk.Label(self, image=self.bg_photo)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not load background: {e}")
            self.configure(bg="#f5f7fa")

        # === Help Button ===
        ttk.Button(self, text="?", width=3, command=self.show_readme).place(relx=1.0, rely=0.0, anchor="ne", x=-10, y=10)

        # === Input Frame ===
        input_frame = ttk.Frame(self)
        input_frame.pack(pady=(60, 10))  # Adjust y-padding to sit under the title
        tk.Label(input_frame, text="Enter City Name:", font=("Segoe UI", 12), fg="white", bg=None).grid(row=0, column=0, padx=5)
        
        # === Create UI elements over image ===
        self.city_var = tk.StringVar()
        self.city_entry = ttk.Entry(input_frame, textvariable=self.city_var, font=("Segoe UI", 12), width=20)
        self.city_entry.grid(row=0, column=1, padx=5)
        self.city_entry.bind("<Return>", lambda event: self.get_weather())
        self.city_entry.bind("<KeyRelease>", self.on_city_typing)

        # === Autocomplete Listbox ===
        self.suggestion_box = tk.Listbox(self, font=("Segoe UI", 11), height=4)
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_suggestion_select)
        self.suggestion_box.place_forget()

        # === Custom Button ===
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.TButton", font=("Segoe UI", 12, "bold"), foreground="white", background="#0078D7", padding=10)
        style.map("Custom.TButton", background=[("active", "#005A9E"), ("pressed", "#003E73")])

        self.get_weather_btn = ttk.Button(self, text="Get Weather", style="Custom.TButton", command=self.get_weather)
        self.get_weather_btn.pack(pady=10)

        # === Result ===
        self.result = tk.Label(self, text="", font=("Segoe UI", 12), justify="center", wraplength=380, bg=None, fg="white")
        self.result.pack(pady=10, fill="both", expand=True)

        self.city_list = [
            "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Tokyo", "London",
            "Paris", "New York", "Los Angeles", "Beijing", "Shanghai", "Hong Kong",
            "Singapore", "Berlin", "Moscow", "Toronto", "Vancouver", "Chicago", "San Francisco"
        ]

    def show_readme(self):
        readme_content = """
Weather App - v1.0

A simple, modern Python desktop app to check the current weather for any city using the Open-Meteo API.

Features:
- Autocomplete for major cities
- Weather condition, temperature, wind speed
- Caching for faster repeat queries
- Transparent look over background image

Install dependencies:
    pip install requests python-dateutil Pillow
        """
        win = tk.Toplevel(self)
        win.title("README")
        win.geometry("600x400")
        txt = tk.Text(win, wrap=tk.WORD, font=("Segoe UI", 10))
        txt.pack(expand=True, fill=tk.BOTH)
        scroll = ttk.Scrollbar(win, command=txt.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt.config(yscrollcommand=scroll.set)
        txt.insert(tk.END, readme_content)
        txt.config(state=tk.DISABLED)

    def on_city_typing(self, event):
        typed = self.city_var.get().strip().lower()
        if not typed:
            self.suggestion_box.place_forget()
            return
        matches = [c for c in self.city_list if c.lower().startswith(typed)]
        if matches:
            self.suggestion_box.delete(0, tk.END)
            for c in matches:
                self.suggestion_box.insert(tk.END, c)
            x = self.city_entry.winfo_rootx() - self.winfo_rootx()
            y = self.city_entry.winfo_rooty() - self.winfo_rooty() + self.city_entry.winfo_height()
            self.suggestion_box.place(x=x, y=y, width=self.city_entry.winfo_width())
            self.suggestion_box.lift()
        else:
            self.suggestion_box.place_forget()

    def on_suggestion_select(self, event):
        if self.suggestion_box.curselection():
            selected = self.suggestion_box.get(self.suggestion_box.curselection())
            self.city_var.set(selected)
            self.suggestion_box.place_forget()
            self.city_entry.icursor(tk.END)
            self.city_entry.focus()

    def get_weather(self):
        city = self.city_var.get().strip()
        if not city:
            messagebox.showwarning("Input Error", "Please enter a city name.")
            return
        self.suggestion_box.place_forget()
        try:
            cache = load_cache(city)
            if cache:
                self.display_weather(city, cache['temperature'], cache['windspeed'], cache['weather'], cached=True)
                return
        except Exception as e:
            print(f"Cache load failed: {e}")
        try:
            geo_resp = requests.get(API_GEO_URL, params={"name": city}, timeout=10)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()
            if not geo_data.get("results"):
                messagebox.showerror("Not Found", f"City '{city}' not found.")
                return
            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]
        except Exception as e:
            messagebox.showerror("Geocoding Error", str(e))
            return
        try:
            weather_resp = requests.get(API_WEATHER_URL, params={"latitude": lat, "longitude": lon, "current_weather": True}, timeout=10)
            weather_resp.raise_for_status()
            data = weather_resp.json()
            current = data.get("current_weather")
            if not current:
                messagebox.showerror("No Data", "Weather data unavailable.")
                return
            temp = current["temperature"]
            wind = current["windspeed"]
            desc = get_weather_desc(current["weathercode"])
            self.display_weather(city, temp, wind, desc)
            save_cache(city, {"city": city, "temperature": temp, "windspeed": wind, "weather": desc})
        except Exception as e:
            messagebox.showerror("Weather Error", str(e))

    def display_weather(self, city, temp, windspeed, desc, cached=False):
        suffix = " (cached)" if cached else ""
        text = f"Current weather in {city}{suffix}:\nTemperature: {temp} °C\nWind Speed: {windspeed} km/h\nWeather: {desc}"
        self.result.config(text=text)

# =========================

if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
