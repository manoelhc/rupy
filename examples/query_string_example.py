#!/usr/bin/env python3
"""
Example demonstrating query string handling in Rupy.

This example shows how to use the new query string methods:
- get_query_keys(): Get all query parameter keys
- get_path_without_query(): Get the path without query string
- get_query_param(key): Get a specific query parameter value
- query_params: Property to get all query parameters as a dict
"""
from __future__ import annotations

from rupy import Request
from rupy import Response
from rupy import Rupy

app = Rupy()


@app.route('/', methods=['GET'])
def index(request: Request) -> Response:
    """Root endpoint with instructions."""
    return Response("""
Query String Example

Try these endpoints:
- /info?name=John&age=30&city=NYC
- /search?q=python&page=2&limit=20
- /keys?foo=bar&baz=qux
- /clean-path?param1=value1&param2=value2
""")


@app.route('/info', methods=['GET'])
def info_handler(request: Request) -> Response:
    """Demonstrate accessing query parameters."""
    # Get specific parameters
    name = request.get_query_param('name') or 'Guest'
    age = request.get_query_param('age') or 'Unknown'
    city = request.get_query_param('city') or 'Unknown'

    # Get all parameters
    all_params = request.query_params

    response_text = f"""
Query Parameter Info:
- Name: {name}
- Age: {age}
- City: {city}

All parameters: {dict(all_params)}
"""
    return Response(response_text)


@app.route('/search', methods=['GET'])
def search_handler(request: Request) -> Response:
    """Demonstrate a search endpoint with query parameters."""
    query = request.get_query_param('q')
    page = request.get_query_param('page') or '1'
    limit = request.get_query_param('limit') or '10'

    if not query:
        return Response("Error: 'q' parameter is required", status=400)

    response_text = f"""
Search Results:
- Query: {query}
- Page: {page}
- Limit: {limit}

Searching for "{query}"... (page {page}, showing {limit} results)
"""
    return Response(response_text)


@app.route('/keys', methods=['GET'])
def keys_handler(request: Request) -> Response:
    """Demonstrate getting query parameter keys."""
    keys = request.get_query_keys()

    response_text = f"""
Query Parameter Keys:
{', '.join(keys) if keys else 'No query parameters'}

Total: {len(keys)} keys
"""
    return Response(response_text)


@app.route('/clean-path', methods=['GET'])
def clean_path_handler(request: Request) -> Response:
    """Demonstrate getting path without query string."""
    full_path = request.path
    clean_path = request.get_path_without_query()

    response_text = f"""
Path Information:
- Full path: {full_path}
- Clean path: {clean_path}
- Has query string: {'Yes' if '?' in full_path else 'No'}
"""
    return Response(response_text)


@app.route('/filter', methods=['GET'])
def filter_handler(request: Request) -> Response:
    """Demonstrate a filtering endpoint."""
    # Get filter parameters
    category = request.get_query_param('category') or 'all'
    min_price = request.get_query_param('min_price') or '0'
    max_price = request.get_query_param('max_price') or 'unlimited'
    sort = request.get_query_param('sort') or 'relevance'

    # Get all parameters to show what was provided
    all_params = request.query_params

    response_text = f"""
Product Filter:
- Category: {category}
- Min Price: {min_price}
- Max Price: {max_price}
- Sort By: {sort}

All filters applied: {dict(all_params)}
"""
    return Response(response_text)


if __name__ == '__main__':
    print('=' * 80)
    print('Query String Example')
    print('=' * 80)
    print('\nStarting server on http://127.0.0.1:8000')
    print('\nTry these URLs:')
    print('  http://127.0.0.1:8000/')
    print('  http://127.0.0.1:8000/info?name=Alice&age=25&city=Seattle')
    print('  http://127.0.0.1:8000/search?q=python&page=1&limit=10')
    print('  http://127.0.0.1:8000/keys?foo=bar&baz=qux&test=123')
    print('  http://127.0.0.1:8000/clean-path?param1=value1&param2=value2')
    print('  http://127.0.0.1:8000/filter?category=electronics&min_price=100&max_price=500&sort=price')
    print('\n' + '=' * 80)
    print()

    app.run(host='127.0.0.1', port=8000)
