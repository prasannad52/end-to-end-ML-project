# Use the official Python 3.9 image as a base
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Hugging Face Spaces uses (7860 by default)
EXPOSE 7860

# Command to run the Flask app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
