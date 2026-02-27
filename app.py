import csv
import io
import hashlib
import functools
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import get_db, init_db

app = Flask(__name__)
app.secret_key = 'salon-influencer-manager-secret-key-2026'

# ─── パスワード設定 ───
# SHA256ハッシュで保存（デフォルト: "coollabo2026"）
APP_PASSWORD_HASH = hashlib.sha256('coollabo2026'.encode()).hexdigest()

PLATFORMS = ['Instagram', 'YouTube', 'TikTok', 'X', 'ブログ', 'LINE']
GENRES = ['美容', 'ファッション', 'ライフスタイル', 'ダイエット', 'ボディメイク',
          'グルメ', '旅行', 'ママ・子育て', '健康・ウェルネス', 'その他']
SUB_GENRES = ['スキンケア', 'メイク', 'ヘアケア', 'ボディケア', 'エステ・サロン',
              '筋トレ', 'ヨガ・ピラティス', '食事管理', '横浜グルメ', 'その他']
STATUSES = ['未連絡', 'DM済', '交渉中', 'コラボ決定', '完了', '見送り']
DM_STATUSES = ['送信済', '既読', '返信あり', '未返信']
COLLAB_STATUSES = ['進行中', '完了', 'キャンセル']
COMPENSATION_TYPES = ['無料施術', '金銭', '物品', '無料施術+金銭', 'その他']
PRIORITIES = ['高', '中', '低']
AGE_GROUPS = ['10代', '20代前半', '20代後半', '30代前半', '30代後半', '40代', '50代以上']
GENDERS = ['女性', '男性', 'その他']
POST_TYPES = ['フィード投稿', 'リール', 'ストーリーズ', 'YouTube動画', 'YouTubeショート',
              'TikTok動画', 'ブログ記事', 'ライブ配信', 'その他']
SOURCES = ['Instagram検索', 'YouTube検索', 'TikTok検索', 'X検索', 'Google検索',
           '紹介', '問い合わせ', 'イベント', 'その他']

DM_TEMPLATES = [
    {
        'name': '初回コラボ提案（脂肪冷却）',
        'content': '''はじめまして。横浜・センター南にある脂肪冷却＆バストケア専門サロン「CoolLabo 港北センター南店」と申します。

{name}様の投稿をいつも拝見しており、美容への意識の高さやフォロワーの皆様への影響力に大変感銘を受けております。

つきましては、当サロンの脂肪冷却施術を体験していただき、その効果をSNSでご紹介いただけないかと考えております。

【ご提案内容】
・脂肪冷却施術を無料でご体験（通常1回 ¥XX,XXX）
・施術後のお写真・動画をSNSでご投稿

ご興味がございましたら、お気軽にご返信ください。
詳細をご案内させていただきます。

CoolLabo 港北センター南店
横浜市都筑区茅ケ崎中央19-4 エルムビルⅡ 2F''',
    },
    {
        'name': '初回コラボ提案（バストケア）',
        'content': '''はじめまして。横浜・センター南にある脂肪冷却＆バストケア専門サロン「CoolLabo 港北センター南店」と申します。

{name}様の発信される美容情報にいつも注目しております。

当サロンでは「育乳トリートメント」という特別なバストケアメニューをご提供しており、ぜひ{name}様に体験していただきたくご連絡いたしました。

【ご提案内容】
・育乳トリートメントを無料でご体験
・施術の様子やビフォーアフターをSNSでご投稿

ご興味がございましたら、ぜひお気軽にご返信ください。

CoolLabo 港北センター南店
横浜市都筑区茅ケ崎中央19-4 エルムビルⅡ 2F''',
    },
    {
        'name': 'フォローアップ（返信なし）',
        'content': '''先日はメッセージをお送りさせていただきありがとうございます。
CoolLabo 港北センター南店です。

お忙しいところ恐れ入りますが、先日のコラボレーションのご提案について、ご検討いただけましたでしょうか。

ご不明な点やご要望がございましたら、お気軽にお申し付けください。
{name}様のご都合の良いタイミングでご返信いただければ幸いです。

CoolLabo 港北センター南店''',
    },
    {
        'name': 'コラボ詳細案内',
        'content': '''{name}様

ご返信ありがとうございます！
CoolLabo 港北センター南店です。

コラボレーションの詳細をご案内いたします。

【施術内容】
・脂肪冷却施術（ご希望の部位1箇所）
・所要時間：約60分

【ご来店について】
・場所：横浜市都筑区茅ケ崎中央19-4 エルムビルⅡ 2F
  （横浜市営地下鉄 センター南駅 徒歩3分）
・ご都合の良い日時を3候補ほどお知らせください

【投稿について】
・施術体験の感想をSNSに投稿いただけると幸いです
・投稿時期：施術後1週間以内
・ハッシュタグ：#CoolLabo #クールラボ #脂肪冷却 #センター南

ご不明な点がございましたらお気軽にお問い合わせください。

CoolLabo 港北センター南店''',
    },
    {
        'name': 'お礼メッセージ（投稿後）',
        'content': '''{name}様

素敵な投稿をしていただき、誠にありがとうございます！
CoolLabo 港北センター南店です。

{name}様の投稿を拝見し、スタッフ一同大変嬉しく思っております。

今後もぜひ継続的にお付き合いいただければ幸いです。
新メニューや季節限定のキャンペーンなど、随時ご案内させていただきます。

引き続きよろしくお願いいたします。

CoolLabo 港北センター南店''',
    },
]


# ─── 認証 ───
def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if hashlib.sha256(password.encode()).hexdigest() == APP_PASSWORD_HASH:
            session['logged_in'] = True
            flash('ログインしました', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('パスワードが正しくありません', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('ログアウトしました', 'info')
    return redirect(url_for('login'))


# ─── ダッシュボード ───
@app.route('/')
@login_required
def dashboard():
    db = get_db()
    total = db.execute('SELECT COUNT(*) as cnt FROM influencers').fetchone()['cnt']
    paid_count = db.execute("SELECT COUNT(*) as cnt FROM influencers WHERE is_paid = 1").fetchone()['cnt']
    free_count = total - paid_count
    status_counts = db.execute(
        'SELECT status, COUNT(*) as cnt FROM influencers GROUP BY status'
    ).fetchall()
    platform_counts = db.execute(
        'SELECT platform, COUNT(*) as cnt FROM influencers GROUP BY platform ORDER BY cnt DESC'
    ).fetchall()
    recent_dms = db.execute(
        '''SELECT d.*, i.name as influencer_name
           FROM dm_history d JOIN influencers i ON d.influencer_id = i.id
           ORDER BY d.sent_at DESC LIMIT 5'''
    ).fetchall()
    active_collabs = db.execute(
        '''SELECT c.*, i.name as influencer_name
           FROM collaborations c JOIN influencers i ON c.influencer_id = i.id
           WHERE c.status = '進行中' ORDER BY c.start_date DESC'''
    ).fetchall()
    upcoming_actions = db.execute(
        '''SELECT id, name, next_action, next_action_date, status
           FROM influencers
           WHERE next_action IS NOT NULL AND next_action != ''
           ORDER BY next_action_date ASC LIMIT 5'''
    ).fetchall()
    db.close()
    return render_template('dashboard.html',
                           total=total, paid_count=paid_count, free_count=free_count,
                           status_counts=status_counts,
                           platform_counts=platform_counts,
                           recent_dms=recent_dms,
                           active_collabs=active_collabs,
                           upcoming_actions=upcoming_actions)


# ─── インフルエンサー CRUD ───
@app.route('/influencers')
@login_required
def influencer_list():
    db = get_db()
    query = 'SELECT * FROM influencers WHERE 1=1'
    params = []

    search = request.args.get('search', '')
    platform = request.args.get('platform', '')
    genre = request.args.get('genre', '')
    status = request.args.get('status', '')
    is_paid = request.args.get('is_paid', '')
    priority = request.args.get('priority', '')

    if search:
        query += ' AND (name LIKE ? OR account_id LIKE ? OR tags LIKE ?)'
        params += [f'%{search}%', f'%{search}%', f'%{search}%']
    if platform:
        query += ' AND platform = ?'
        params.append(platform)
    if genre:
        query += ' AND genre = ?'
        params.append(genre)
    if status:
        query += ' AND status = ?'
        params.append(status)
    if is_paid == '1':
        query += ' AND is_paid = 1'
    elif is_paid == '0':
        query += ' AND is_paid = 0'
    if priority:
        query += ' AND priority = ?'
        params.append(priority)

    query += ' ORDER BY updated_at DESC'
    influencers = db.execute(query, params).fetchall()
    db.close()
    return render_template('influencers/list.html',
                           influencers=influencers,
                           platforms=PLATFORMS, genres=GENRES, statuses=STATUSES,
                           priorities=PRIORITIES,
                           search=search, sel_platform=platform,
                           sel_genre=genre, sel_status=status,
                           sel_is_paid=is_paid, sel_priority=priority)


@app.route('/influencers/new', methods=['GET', 'POST'])
@login_required
def influencer_new():
    if request.method == 'POST':
        db = get_db()
        db.execute(
            '''INSERT INTO influencers (name, platform, account_id, follower_count,
               engagement_rate, genre, sub_genre, area, age_group, gender,
               contact_info, email, phone, website_url,
               is_paid, priority, rating, notes, tags,
               next_action, next_action_date, source, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            [request.form['name'], request.form['platform'],
             request.form.get('account_id', ''),
             int(request.form.get('follower_count') or 0),
             float(request.form.get('engagement_rate') or 0),
             request.form.get('genre', ''),
             request.form.get('sub_genre', ''),
             request.form.get('area', ''),
             request.form.get('age_group', ''),
             request.form.get('gender', ''),
             request.form.get('contact_info', ''),
             request.form.get('email', ''),
             request.form.get('phone', ''),
             request.form.get('website_url', ''),
             1 if request.form.get('is_paid') else 0,
             request.form.get('priority', '中'),
             int(request.form.get('rating') or 3),
             request.form.get('notes', ''),
             request.form.get('tags', ''),
             request.form.get('next_action', ''),
             request.form.get('next_action_date') or None,
             request.form.get('source', ''),
             request.form.get('status', '未連絡')]
        )
        db.commit()
        db.close()
        flash('インフルエンサーを登録しました', 'success')
        return redirect(url_for('influencer_list'))
    return render_template('influencers/form.html',
                           influencer=None, platforms=PLATFORMS,
                           genres=GENRES, sub_genres=SUB_GENRES,
                           statuses=STATUSES, priorities=PRIORITIES,
                           age_groups=AGE_GROUPS, genders=GENDERS,
                           sources=SOURCES)


@app.route('/influencers/<int:id>')
@login_required
def influencer_detail(id):
    db = get_db()
    inf = db.execute('SELECT * FROM influencers WHERE id = ?', [id]).fetchone()
    if not inf:
        db.close()
        flash('インフルエンサーが見つかりません', 'danger')
        return redirect(url_for('influencer_list'))
    dms = db.execute(
        'SELECT * FROM dm_history WHERE influencer_id = ? ORDER BY sent_at DESC', [id]
    ).fetchall()
    collabs = db.execute(
        'SELECT * FROM collaborations WHERE influencer_id = ? ORDER BY start_date DESC', [id]
    ).fetchall()
    db.close()
    return render_template('influencers/detail.html',
                           influencer=inf, dms=dms, collabs=collabs)


@app.route('/influencers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def influencer_edit(id):
    db = get_db()
    if request.method == 'POST':
        db.execute(
            '''UPDATE influencers SET name=?, platform=?, account_id=?,
               follower_count=?, engagement_rate=?, genre=?, sub_genre=?,
               area=?, age_group=?, gender=?,
               contact_info=?, email=?, phone=?, website_url=?,
               is_paid=?, priority=?, rating=?, notes=?, tags=?,
               next_action=?, next_action_date=?, source=?,
               status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?''',
            [request.form['name'], request.form['platform'],
             request.form.get('account_id', ''),
             int(request.form.get('follower_count') or 0),
             float(request.form.get('engagement_rate') or 0),
             request.form.get('genre', ''),
             request.form.get('sub_genre', ''),
             request.form.get('area', ''),
             request.form.get('age_group', ''),
             request.form.get('gender', ''),
             request.form.get('contact_info', ''),
             request.form.get('email', ''),
             request.form.get('phone', ''),
             request.form.get('website_url', ''),
             1 if request.form.get('is_paid') else 0,
             request.form.get('priority', '中'),
             int(request.form.get('rating') or 3),
             request.form.get('notes', ''),
             request.form.get('tags', ''),
             request.form.get('next_action', ''),
             request.form.get('next_action_date') or None,
             request.form.get('source', ''),
             request.form.get('status', '未連絡'), id]
        )
        db.commit()
        db.close()
        flash('インフルエンサー情報を更新しました', 'success')
        return redirect(url_for('influencer_detail', id=id))
    inf = db.execute('SELECT * FROM influencers WHERE id = ?', [id]).fetchone()
    db.close()
    if not inf:
        flash('インフルエンサーが見つかりません', 'danger')
        return redirect(url_for('influencer_list'))
    return render_template('influencers/form.html',
                           influencer=inf, platforms=PLATFORMS,
                           genres=GENRES, sub_genres=SUB_GENRES,
                           statuses=STATUSES, priorities=PRIORITIES,
                           age_groups=AGE_GROUPS, genders=GENDERS,
                           sources=SOURCES)


@app.route('/influencers/<int:id>/delete', methods=['POST'])
@login_required
def influencer_delete(id):
    db = get_db()
    db.execute('DELETE FROM influencers WHERE id = ?', [id])
    db.commit()
    db.close()
    flash('インフルエンサーを削除しました', 'info')
    return redirect(url_for('influencer_list'))


@app.route('/influencers/import', methods=['POST'])
@login_required
def influencer_import():
    file = request.files.get('csv_file')
    if not file or not file.filename.endswith('.csv'):
        flash('CSVファイルを選択してください', 'danger')
        return redirect(url_for('influencer_list'))

    stream = io.TextIOWrapper(file.stream, encoding='utf-8-sig')
    reader = csv.DictReader(stream)
    db = get_db()
    count = 0
    for row in reader:
        db.execute(
            '''INSERT INTO influencers (name, platform, account_id, follower_count,
               engagement_rate, genre, sub_genre, area, age_group, gender,
               contact_info, email, phone, website_url,
               is_paid, priority, notes, tags, source, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            [row.get('name', ''), row.get('platform', ''),
             row.get('account_id', ''),
             int(row.get('follower_count') or 0),
             float(row.get('engagement_rate') or 0),
             row.get('genre', ''), row.get('sub_genre', ''),
             row.get('area', ''), row.get('age_group', ''),
             row.get('gender', ''),
             row.get('contact_info', ''), row.get('email', ''),
             row.get('phone', ''), row.get('website_url', ''),
             1 if row.get('is_paid', '').strip() in ('1', 'true', 'TRUE', 'はい') else 0,
             row.get('priority', '中'),
             row.get('notes', ''), row.get('tags', ''),
             row.get('source', ''), row.get('status', '未連絡')]
        )
        count += 1
    db.commit()
    db.close()
    flash(f'{count}件のインフルエンサーをインポートしました', 'success')
    return redirect(url_for('influencer_list'))


# ─── DM管理 ───
@app.route('/dm')
@login_required
def dm_history():
    db = get_db()
    dms = db.execute(
        '''SELECT d.*, i.name as influencer_name, i.platform
           FROM dm_history d JOIN influencers i ON d.influencer_id = i.id
           ORDER BY d.sent_at DESC'''
    ).fetchall()
    influencers = db.execute(
        'SELECT id, name, platform FROM influencers ORDER BY name'
    ).fetchall()
    db.close()
    return render_template('dm/history.html',
                           dms=dms, influencers=influencers,
                           dm_statuses=DM_STATUSES,
                           templates=DM_TEMPLATES)


@app.route('/dm/add', methods=['POST'])
@login_required
def dm_add():
    db = get_db()

    influencer_id = request.form['influencer_id']
    inf = db.execute('SELECT name FROM influencers WHERE id = ?', [influencer_id]).fetchone()
    message = request.form.get('message_content', '')
    if inf:
        message = message.replace('{name}', inf['name'])

    db.execute(
        '''INSERT INTO dm_history (influencer_id, message_content, direction, status)
           VALUES (?, ?, ?, ?)''',
        [influencer_id, message,
         request.form.get('direction', '送信'),
         request.form.get('status', '送信済')]
    )
    db.execute(
        "UPDATE influencers SET status = 'DM済', last_contact_date = DATE('now'), updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = '未連絡'",
        [influencer_id]
    )
    db.commit()
    db.close()
    flash('DM履歴を記録しました', 'success')
    return redirect(url_for('dm_history'))


@app.route('/dm/<int:id>/update_status', methods=['POST'])
@login_required
def dm_update_status(id):
    db = get_db()
    new_status = request.form['status']
    db.execute('UPDATE dm_history SET status = ? WHERE id = ?', [new_status, id])
    db.commit()
    db.close()
    flash('DMステータスを更新しました', 'success')
    return redirect(url_for('dm_history'))


# ─── コラボレーション管理 ───
@app.route('/collaborations')
@login_required
def collaboration_list():
    db = get_db()
    collabs = db.execute(
        '''SELECT c.*, i.name as influencer_name, i.platform
           FROM collaborations c JOIN influencers i ON c.influencer_id = i.id
           ORDER BY c.created_at DESC'''
    ).fetchall()
    influencers = db.execute(
        'SELECT id, name, platform FROM influencers ORDER BY name'
    ).fetchall()
    db.close()
    return render_template('collaborations/list.html',
                           collabs=collabs, influencers=influencers,
                           collab_statuses=COLLAB_STATUSES,
                           compensation_types=COMPENSATION_TYPES,
                           post_types=POST_TYPES)


@app.route('/collaborations/add', methods=['POST'])
@login_required
def collaboration_add():
    db = get_db()
    db.execute(
        '''INSERT INTO collaborations (influencer_id, title, description, start_date, end_date,
           compensation_type, compensation_amount, post_url, post_type, deliverables, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        [request.form['influencer_id'], request.form['title'],
         request.form.get('description', ''),
         request.form.get('start_date') or None,
         request.form.get('end_date') or None,
         request.form.get('compensation_type', ''),
         request.form.get('compensation_amount', ''),
         request.form.get('post_url', ''),
         request.form.get('post_type', ''),
         request.form.get('deliverables', ''),
         request.form.get('status', '進行中')]
    )
    db.execute(
        "UPDATE influencers SET status = 'コラボ決定', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [request.form['influencer_id']]
    )
    db.commit()
    db.close()
    flash('コラボレーションを登録しました', 'success')
    return redirect(url_for('collaboration_list'))


@app.route('/collaborations/<int:id>/update', methods=['POST'])
@login_required
def collaboration_update(id):
    db = get_db()
    db.execute(
        '''UPDATE collaborations SET title=?, description=?, start_date=?, end_date=?,
           compensation_type=?, compensation_amount=?, post_url=?, post_type=?,
           deliverables=?, status=? WHERE id=?''',
        [request.form['title'],
         request.form.get('description', ''),
         request.form.get('start_date') or None,
         request.form.get('end_date') or None,
         request.form.get('compensation_type', ''),
         request.form.get('compensation_amount', ''),
         request.form.get('post_url', ''),
         request.form.get('post_type', ''),
         request.form.get('deliverables', ''),
         request.form.get('status', '進行中'), id]
    )
    db.commit()
    db.close()
    flash('コラボレーション情報を更新しました', 'success')
    return redirect(url_for('collaboration_list'))


@app.route('/collaborations/<int:id>/delete', methods=['POST'])
@login_required
def collaboration_delete(id):
    db = get_db()
    db.execute('DELETE FROM collaborations WHERE id = ?', [id])
    db.commit()
    db.close()
    flash('コラボレーションを削除しました', 'info')
    return redirect(url_for('collaboration_list'))


# ─── 効果測定レポート ───
@app.route('/reports')
@login_required
def reports():
    db = get_db()
    results = db.execute(
        '''SELECT cr.*, c.title as collab_title, i.name as influencer_name, i.platform
           FROM collaboration_results cr
           JOIN collaborations c ON cr.collaboration_id = c.id
           JOIN influencers i ON c.influencer_id = i.id
           ORDER BY cr.measured_at DESC'''
    ).fetchall()
    collabs = db.execute(
        '''SELECT c.id, c.title, i.name as influencer_name
           FROM collaborations c JOIN influencers i ON c.influencer_id = i.id
           ORDER BY c.created_at DESC'''
    ).fetchall()

    influencer_stats = db.execute(
        '''SELECT i.name, i.platform,
                  COUNT(DISTINCT c.id) as collab_count,
                  COALESCE(SUM(cr.views), 0) as total_views,
                  COALESCE(SUM(cr.likes), 0) as total_likes,
                  COALESCE(SUM(cr.new_customers), 0) as total_customers,
                  COALESCE(SUM(cr.revenue_impact), 0) as total_revenue
           FROM influencers i
           JOIN collaborations c ON c.influencer_id = i.id
           LEFT JOIN collaboration_results cr ON cr.collaboration_id = c.id
           GROUP BY i.id
           ORDER BY total_revenue DESC'''
    ).fetchall()

    db.close()
    return render_template('reports/dashboard.html',
                           results=results, collabs=collabs,
                           influencer_stats=influencer_stats)


@app.route('/reports/add', methods=['POST'])
@login_required
def report_add():
    db = get_db()
    db.execute(
        '''INSERT INTO collaboration_results
           (collaboration_id, views, likes, comments, shares, saves,
            new_followers, new_customers, coupon_uses, revenue_impact, measured_at, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        [request.form['collaboration_id'],
         int(request.form.get('views') or 0),
         int(request.form.get('likes') or 0),
         int(request.form.get('comments') or 0),
         int(request.form.get('shares') or 0),
         int(request.form.get('saves') or 0),
         int(request.form.get('new_followers') or 0),
         int(request.form.get('new_customers') or 0),
         int(request.form.get('coupon_uses') or 0),
         int(request.form.get('revenue_impact') or 0),
         request.form.get('measured_at') or None,
         request.form.get('notes', '')]
    )
    db.commit()
    db.close()
    flash('効果測定データを記録しました', 'success')
    return redirect(url_for('reports'))


@app.route('/reports/<int:id>/delete', methods=['POST'])
@login_required
def report_delete(id):
    db = get_db()
    db.execute('DELETE FROM collaboration_results WHERE id = ?', [id])
    db.commit()
    db.close()
    flash('効果測定データを削除しました', 'info')
    return redirect(url_for('reports'))


# ─── API（Chart.js用） ───
@app.route('/api/report_data')
@login_required
def api_report_data():
    db = get_db()
    stats = db.execute(
        '''SELECT i.name,
                  COALESCE(SUM(cr.views), 0) as views,
                  COALESCE(SUM(cr.likes), 0) as likes,
                  COALESCE(SUM(cr.comments), 0) as comments,
                  COALESCE(SUM(cr.new_customers), 0) as customers,
                  COALESCE(SUM(cr.revenue_impact), 0) as revenue
           FROM influencers i
           JOIN collaborations c ON c.influencer_id = i.id
           LEFT JOIN collaboration_results cr ON cr.collaboration_id = c.id
           GROUP BY i.id
           HAVING (views + likes + comments + customers + revenue) > 0
           ORDER BY revenue DESC'''
    ).fetchall()
    db.close()
    return jsonify({
        'labels': [r['name'] for r in stats],
        'views': [r['views'] for r in stats],
        'likes': [r['likes'] for r in stats],
        'comments': [r['comments'] for r in stats],
        'customers': [r['customers'] for r in stats],
        'revenue': [r['revenue'] for r in stats],
    })


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
