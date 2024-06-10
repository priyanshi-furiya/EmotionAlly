## EmotionAlly Chatbot

EmotionAlly is a compassionate mental health assistant chatbot designed to provide support and information related to mental health. This project utilizes Azure OpenAI's GPT-3.5-turbo for natural language understanding and response generation, and a SQLite database to store user interactions. The application is built with Flask and integrates several functionalities, including user authentication and querying mental health resources.

Deployment link - https://project-emotionally.azurewebsites.net/

### Features
- **User Authentication**: Users can sign up and log in to their accounts.
- **Speech Recognition**: Integrates Web Speech API for speech-to-text conversion directly in the browser.
- **Natural Language Processing**: Uses GPT-3.5-turbo for generating conversational responses.
- **Mental Health Resource Querying**: Retrieves relevant information from preloaded datasets based on user queries.
- **Data Storage**: Stores user interactions in a SQLite database for personalized responses.
- 
### Installation

#### Prerequisites
- Python 3.x
- pip (Python package installer)

#### Steps

1. **Clone the repository**:
    ```sh
    git clone https://github.com/your-username/emotionally.git
    cd emotionally
    ```

2. **Set up a virtual environment** (recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Set up the database**:
    - SQLite database is automatically set up when you run the application.

5. **Set up Azure OpenAI credentials**:
    - Set your Azure OpenAI API endpoint and key in `app.py`:
    ```python
    endpoint = "https://your-openai-endpoint.azure.com/"
    api_key = "your-api-key"
    ```

6. **Run the application**:
    ```sh
    python app.py
    ```

7. **Access the application**:
    - Open your web browser and navigate to `http://localhost:8000`.

### Usage

#### User Authentication
- **Sign Up**: Create a new user account by providing a username, email, age, gender, and password.
- **Log In**: Access your account by entering your username and password.

#### Chat Functionality
- **Text Input**: Type your message and click "Send" to get a response from the chatbot.
- **Audio Input**: Click the "Audio" button to speak your query and get a response.

### Dataset and Embeddings
- **NHS Data**: Information from NHS related to mental health.
- **Mind Data**: Information from Mind, a mental health charity.
- **Mental Health FAQs**: Frequently asked questions about mental health.

The embeddings for these datasets are pre-generated using the Azure OpenAI API and stored for quick access during queries.

### Development
#### Adding New Features
1. **Front-End Changes**: Modify HTML/CSS/JavaScript files in the `templates` and `static` directories.
2. **Back-End Changes**: Update `app.py` to add new routes or modify existing functionalities.

#### Database Schema
- The SQLite database (`chatbot.db`) contains a `messages` table to store user and assistant interactions.
- User credentials and details are stored in an Azure SQL database.

#### API Integration
- **Azure OpenAI API**: Used for generating responses and embeddings.

### License
This project is licensed under the MIT License.

### Contact
For any questions or suggestions, please contact [furiyapriyanshi@gmail.com].
