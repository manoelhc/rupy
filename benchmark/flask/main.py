from flask import Flask

# Create a Flask application instance.
# __name__ is a convenient shortcut for the module's name,
# which Flask uses to locate resources like templates and static files.
app = Flask(__name__)

# Define a route for the root URL ('/').
# The @app.route('/') decorator associates the 'hello_world' function
# with the specified URL path.
@app.route('/')
def hello_world():
    """
    This function is called when a request is made to the root URL.
    It returns a simple HTML string as the response.
    """
    return "<p>Hello, World!</p>"

# This block ensures the development server runs only when the script is executed directly.
if __name__ == '__main__':
    # Run the Flask development server.
    # debug=True enables debug mode, which provides detailed error messages
    # and automatically reloads the server on code changes.
    app.run(debug=True)