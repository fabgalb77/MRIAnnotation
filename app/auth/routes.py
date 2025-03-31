from flask import render_template, redirect, url_for, flash, request, session
from app.auth import bp
from app.auth.utils import check_user_credentials, login_required

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    # If user is already logged in, redirect to dashboard
    if 'username' in session:
        return redirect(url_for('main.dashboard'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if check_user_credentials(username, password):
            session['username'] = username
            session.permanent = True
            
            # Get next parameter or default to dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
                
            flash(f'Welcome back, {username}!', 'success')
            return redirect(next_page)
        else:
            error = 'Invalid username or password'
    
    return render_template('auth/login.html', error=error)

@bp.route('/logout')
def logout():
    """Logout route"""
    session.pop('username', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))
