from functools import wraps
from flask import session, redirect, url_for, request
import xml.etree.ElementTree as ET
import os

def access_control_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Ensure user is logged in
        if 'user_level' not in session:
            return redirect(url_for('login'))

        # Load XML configuration
        xml_path = os.path.join('static', 'map_page', 'user_access.xml')  # Make sure this matches your folder
        if not os.path.exists(xml_path):
            return "Access control configuration missing.", 403

        tree = ET.parse(xml_path)
        root = tree.getroot()

        user_level = str(session['user_level'])  # levels are integers, but XML likely uses strings
        current_path = request.path

        for level in root.findall('level'):
            if level.get('id') == user_level:
                for page in level.findall('page'):
                    if current_path.startswith(page.text.strip()):
                        return f(*args, **kwargs)  # ✅ Access granted

        return "Access denied. You do not have permission to access this page.", 403
    return decorated_function
