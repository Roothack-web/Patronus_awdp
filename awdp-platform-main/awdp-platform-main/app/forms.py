from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, IntegerField, FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_wtf.file import FileRequired, FileAllowed


class LoginForm(FlaskForm):
    username = StringField('队伍名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')


class TeamRegisterForm(FlaskForm):
    name = StringField('队伍名', validators=[DataRequired(), Length(min=2, max=64)])
    password = PasswordField('密码', validators=[DataRequired()])
    password2 = PasswordField('重复密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')


class ChallengeForm(FlaskForm):
    title = StringField('题目标题', validators=[DataRequired(), Length(max=140)])
    category = SelectField('类别', choices=[('web', 'Web'), ('pwn', 'PWN')], default='web')
    description = TextAreaField('题目描述', validators=[Length(max=5000)])
    initial_score = IntegerField('初始分值', default=500)
    docker_image = StringField('Docker 镜像', validators=[Length(max=256)])
    docker_port = IntegerField('固定外部端口 (留空自动分配)', default=0)
    internal_port = IntegerField('容器内部端口', default=80)
    min_score = IntegerField('最低分值', default=100)
    score_decay = IntegerField('递减分值', default=50)
    exp_cmd = StringField(
        'EXP 命令 (容器内执行)',
        validators=[Length(max=500)],
        description='运行在容器内的 EXP 命令，{PORT} 会被替换为内部端口。示例: python3 /opt/exp.py --target http://127.0.0.1:{PORT}'
    )
    fix_base_score = IntegerField('修复基础分', default=300)
    max_resets = IntegerField('最大重置次数', default=10)
    enabled = BooleanField('启用 (在前台展示)', default=True)
    is_fixed = BooleanField('已修复 (禁止继续上传防御包)')
    contest_id = SelectField('比赛', coerce=int, choices=[], default=0)
    submit = SubmitField('保存')


class SubmitFlagForm(FlaskForm):
    flag = StringField('Flag', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('提交')


class DefenseUploadForm(FlaskForm):
    package = FileField('防护包 (.tar.gz)', validators=[
        FileRequired(),
        FileAllowed(['gz', 'tar', 'tgz'], '只允许 .tar.gz/.tgz')
    ])
    submit = SubmitField('上传防护包')


class ContestForm(FlaskForm):
    name = StringField('比赛名称', validators=[DataRequired(), Length(max=140)])
    description = TextAreaField('描述', validators=[Length(max=2000)])
    start_at = StringField('开始时间 (ISO格式, 如 2026-05-08T10:00)')
    end_at = StringField('结束时间 (ISO格式, 如 2026-05-08T18:00)')
    submit = SubmitField('保存')


class ContestRoundForm(FlaskForm):
    name = StringField('轮次名称', validators=[DataRequired(), Length(max=140)])
    start_at = StringField('开始时间 (ISO格式)')
    end_at = StringField('结束时间 (ISO格式)')
    multiplier = StringField('得分倍率 (如 1.0)', default='1.0')
    submit = SubmitField('添加轮次')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('当前密码', validators=[DataRequired()])
    new_password = PasswordField('新密码', validators=[DataRequired(), Length(min=4, max=64)])
    new_password2 = PasswordField('重复新密码', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('修改密码')


class ContainerActionForm(FlaskForm):
    submit = SubmitField('确认')
