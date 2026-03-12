# ✈ Trip Smart – Travel & Hotel Recommendation System

Trip Smart is a **Flask-based web application** that helps users plan trips by recommending **transport options (airways, railways, roadways) and hotels** based on the user's route and budget.

The system allows users to search travel options between cities, compare prices, optionally select hotels, and save trips to their account for future reference.

---

# 📌 Features

### User Management

* User registration (Sign Up)
* Secure login system
* Password hashing using **Bcrypt**
* Forgot password functionality
* User profile management

### Travel Planning

* Choose travel mode:

  * ✈ Airways
  * 🚆 Railways
  * 🚌 Roadways
* Select **source city and destination**
* Choose **travel date**
* Optional **budget filtering**

### Transport Recommendation

* Displays available transport options from dataset
* Shows:

  * Transport name
  * Departure and arrival time
  * Price
* Sorts results based on price

### Hotel Recommendation

* Suggests hotels at the destination
* Filters hotels based on **remaining budget**
* Allows skipping hotel selection

### Trip Summary

* Displays final trip summary
* Shows:

  * Selected transport
  * Selected hotel
  * Total cost
  * Budget comparison

### Trip Management

* Save trips to database
* View saved trips
* Delete trips
* Dashboard showing:

  * Total trips
  * Total spending

---

# 🛠 Technologies Used

| Technology   | Purpose                |
| ------------ | ---------------------- |
| Python       | Backend logic          |
| Flask        | Web framework          |
| SQLite       | Database               |
| Pandas       | CSV dataset processing |
| Flask-Bcrypt | Password hashing       |
| HTML         | Page structure         |
| Bootstrap    | Styling and UI         |
| Jinja2       | Template rendering     |

---

# 📊 Datasets Used

The application reads travel and hotel data from CSV files.

| File        | Purpose        |
| ----------- | -------------- |
| airline.csv | Flight options |
| train.csv   | Train routes   |
| bus.csv     | Bus routes     |
| hotel.csv   | Hotel listings |

These datasets are processed using **Pandas**.

---

# ⚙ Installation & Setup

### 1️⃣ Clone the Repository

```
git clone https://github.com/Prathamesh-2003/Trip-Smart.git
```

### 2️⃣ Navigate to the Project Folder

```
cd Trip-Smart
```

### 3️⃣ Install Required Libraries

```
pip install flask
pip install flask-bcrypt
pip install pandas
```

or

```
pip install -r requirements.txt
```

---

# ▶ Running the Application

Start the Flask server:

```
python app.py
```

Then open your browser and go to:

```
http://127.0.0.1:5000
```

---

# 🗄 Database

The application uses **SQLite (`users.db`)**.

Tables used:

### Users

Stores user account information.

```
id
name
username
email
password
```

### Trips

Stores saved trips.

```
id
user_id
mode
from_city
to_city
travel_date
transport_name
hotel_name
total_cost
```

---

# 📈 Future Improvements

Possible improvements for the project:

* Integration with **real travel APIs**
* Machine learning based recommendation system
* Real-time ticket pricing
* Map integration
* Mobile responsive UI improvements
* Deployment on cloud platforms

---

# 👨‍💻 Author

**Pratham Jadhav**

GitHub:
https://github.com/Prathamesh-2003

---

# ⭐ Project Purpose

This project was created as a **Data Science / Web Application project** demonstrating:

* Flask backend development
* CSV data processing using Pandas
* Authentication systems
* Travel recommendation logic
* Database management using SQLite
