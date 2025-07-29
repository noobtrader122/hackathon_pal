# hackathon_pal

**hackathon_pal** is a platform built to streamline and host SQL-based hackathons. Whether you’re an organizer creating challenging problems or a participant eager to show off your SQL skills, hackathon_pal offers all the essential features to run a competitive and engaging online event.

## Features

- Create and manage multiple SQL hackathons.
- User registration and authentication.
- Problem creation with test databases and expected output validation.
- Real-time submission evaluation and leaderboard updates.
- Admin dashboard for managing participants and monitoring progress.

## Getting Started

### Prerequisites

- `Python 3.8+`
- `pip (Python package installer)`
- `Any additional dependencies as specified in requirements.txt`
- `(Optional) Docker, for containerized deployment`

### Installation

1. **Clone the Repository**
   - `git clone https://github.com/noobtrader122/hackathon_pal.git`
   - `cd hackathon_pal`

2. **Install Dependencies**
   - `pip install -r requirements.txt`


3. **Set Up Environment Variables**

   - `Create a .env file and set up required variables such as database URL, secret keys, etc.`

4. **Run Database Migrations**
   - `flask db init`
   - `flask db migrate`
   - `flask db upgrade`


5. **Start the Server**

   - `python app.py`


Visit `http://localhost:5000` to begin!

## Load Testing with Locust

To stress-test your deployment and ensure performance, use Locust:
    locust -f locusttest.py --host=http://localhost:5000


Access the Locust UI at [http://localhost:8089](http://localhost:8089) and start simulating users.

## Contributing

Pull requests and feature suggestions are welcome! Please file issues and contribute on GitHub to help this project grow.

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

Special thanks to all contributors and hackathon participants shaping the future of SQL competitions!

