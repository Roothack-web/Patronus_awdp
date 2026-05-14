from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, login_user, logout_user
from app.models import Team, User
from app.forms import LoginForm, TeamRegisterForm, ChangePasswordForm
from app import db

bp = Blueprint('auth', __name__, template_folder='../templates')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        team = Team.query.filter_by(name=form.username.data).first()
        if team is None or not team.check_password(form.password.data):
            flash('队伍名或密码错误')
            return redirect(url_for('auth.login'))
        login_user(team, remember=form.remember_me.data)
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.dashboard'))
    return render_template('login.html', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Team profile & password change."""
    if not hasattr(current_user, 'name'):
        return redirect(url_for('main.index'))
    form = ChangePasswordForm()
    if form.validate_on_submit():
        team = current_user
        if not team.check_password(form.old_password.data):
            flash('当前密码错误')
            return redirect(url_for('auth.profile'))
        team.set_password(form.new_password.data)
        db.session.commit()
        flash('密码已修改')
        return redirect(url_for('auth.profile'))
    return render_template('profile.html', form=form, team=current_user)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = TeamRegisterForm()
    if form.validate_on_submit():
        existing = Team.query.filter_by(name=form.name.data).first()
        if existing:
            flash('队伍名已存在')
            return render_template('register.html', form=form)
        team = Team(name=form.name.data)
        team.set_password(form.password.data)
        db.session.add(team)
        db.session.commit()
        flash('队伍注册成功，请登录')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)
