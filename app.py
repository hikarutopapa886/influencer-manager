import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from models import get_db, init_db

app = Flask(__name__)
app.secret_key = 'salon-influencer-manager-secret-key'

PLATFORMS = ['Instagram', 'YouTube', 'TikTok', 'X']
GENRES = ['美容', 'ファッション', 'ライフスタイル', 'ダイエット', 'ボディメイク', 'グルメ', '旅行', 'その他']
STATUSES = ['未連絡', 'DM済', '交渉中', 'コラボ決定', '完了', '見送り']
DM_STATUSES = ['送信済', '既読', '返信あり', '未返信']
COLLAB_STATUSES = ['進行中', '完了', 'キャンセル']
COMPENSATION_TYPES = ['無料施術', '金銭', '物品', '無料施術+金銭', 'その他']

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
]


# ─── ダッシュボード ───
@app.route('/')
def dashboard():
    db = get_db()
    total = db.execute('SELECT COUNT(*) as cnt FROM influencers').fetchone()['cnt']
    status_counts = db.execute(
        'SELECT status, COUNT(*) as cnt FROM influencers GROUP BY status'
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
    db.close()
    return render_template('dashboard.html',
                           total=total,
                           status_counts=status_counts,
                           recent_dms=recent_dms,
                           active_collabs=active_collabs)


# ─── インフルエンサー CRUD ───
@app.route('/influencers')
def influencer_list():
    db = get_db()
    query = 'SELECT * FROM influencers WHERE 1=1'
    params = []

    search = request.args.get('search', '')
    platform = request.args.get('platform', '')
    genre = request.args.get('genre', '')
    status = request.args.get('status', '')

    if search:
        query += ' AND (name LIKE ? OR account_id LIKE ?)'
        params += [f'%{search}%', f'%{search}%']
    if platform:
        query += ' AND platform = ?'
        params.append(platform)
    if genre:
        query += ' AND genre = ?'
        params.append(genre)
    if status:
        query += ' AND status = ?'
        params.append(status)

    query += ' ORDER BY updated_at DESC'
    influencers = db.execute(query, params).fetchall()
    db.close()
    return render_template('influencers/list.html',
                           influencers=influencers,
                           platforms=PLATFORMS, genres=GENRES, statuses=STATUSES,
                           search=search, sel_platform=platform,
                           sel_genre=genre, sel_status=status)


@app.route('/influencers/new', methods=['GET', 'POST'])
def influencer_new():
    if request.method == 'POST':
        db = get_db()
        db.execute(
            '''INSERT INTO influencers (name, platform, account_id, follower_count,
               genre, area, contact_info, notes, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            [request.form['name'], request.form['platform'],
             request.form.get('account_id', ''),
             int(request.form.get('follower_count') or 0),
             request.form.get('genre', ''),
             request.form.get('area', ''),
             request.form.get('contact_info', ''),
             request.form.get('notes', ''),
             request.form.get('status', '未連絡')]
        )
        db.commit()
        db.close()
        flash('インフルエンサーを登録しました', 'success')
        return redirect(url_for('influencer_list'))
    return render_template('influencers/form.html',
                           influencer=None, platforms=PLATFORMS,
                           genres=GENRES, statuses=STATUSES)


@app.route('/influencers/<int:id>')
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
def influencer_edit(id):
    db = get_db()
    if request.method == 'POST':
        db.execute(
            '''UPDATE influencers SET name=?, platform=?, account_id=?,
               follower_count=?, genre=?, area=?, contact_info=?, notes=?,
               status=?, updated_at=CURRENT_TIMESTAMP WHERE id=?''',
            [request.form['name'], request.form['platform'],
             request.form.get('account_id', ''),
             int(request.form.get('follower_count') or 0),
             request.form.get('genre', ''),
             request.form.get('area', ''),
             request.form.get('contact_info', ''),
             request.form.get('notes', ''),
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
                           genres=GENRES, statuses=STATUSES)


@app.route('/influencers/<int:id>/delete', methods=['POST'])
def influencer_delete(id):
    db = get_db()
    db.execute('DELETE FROM influencers WHERE id = ?', [id])
    db.commit()
    db.close()
    flash('インフルエンサーを削除しました', 'info')
    return redirect(url_for('influencer_list'))


@app.route('/influencers/import', methods=['POST'])
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
               genre, area, contact_info, notes, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            [row.get('name', ''), row.get('platform', ''),
             row.get('account_id', ''),
             int(row.get('follower_count') or 0),
             row.get('genre', ''), row.get('area', ''),
             row.get('contact_info', ''), row.get('notes', ''),
             row.get('status', '未連絡')]
        )
        count += 1
    db.commit()
    db.close()
    flash(f'{count}件のインフルエンサーをインポートしました', 'success')
    return redirect(url_for('influencer_list'))


# ─── DM管理 ───
@app.route('/dm')
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
    # インフルエンサーのステータスも更新
    db.execute(
        "UPDATE influencers SET status = 'DM済', updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = '未連絡'",
        [influencer_id]
    )
    db.commit()
    db.close()
    flash('DM履歴を記録しました', 'success')
    return redirect(url_for('dm_history'))


@app.route('/dm/<int:id>/update_status', methods=['POST'])
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
                           compensation_types=COMPENSATION_TYPES)


@app.route('/collaborations/add', methods=['POST'])
def collaboration_add():
    db = get_db()
    db.execute(
        '''INSERT INTO collaborations (influencer_id, title, start_date, end_date,
           compensation_type, compensation_amount, post_url, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        [request.form['influencer_id'], request.form['title'],
         request.form.get('start_date') or None,
         request.form.get('end_date') or None,
         request.form.get('compensation_type', ''),
         request.form.get('compensation_amount', ''),
         request.form.get('post_url', ''),
         request.form.get('status', '進行中')]
    )
    # インフルエンサーのステータスを更新
    db.execute(
        "UPDATE influencers SET status = 'コラボ決定', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [request.form['influencer_id']]
    )
    db.commit()
    db.close()
    flash('コラボレーションを登録しました', 'success')
    return redirect(url_for('collaboration_list'))


@app.route('/collaborations/<int:id>/update', methods=['POST'])
def collaboration_update(id):
    db = get_db()
    db.execute(
        '''UPDATE collaborations SET title=?, start_date=?, end_date=?,
           compensation_type=?, compensation_amount=?, post_url=?, status=?
           WHERE id=?''',
        [request.form['title'],
         request.form.get('start_date') or None,
         request.form.get('end_date') or None,
         request.form.get('compensation_type', ''),
         request.form.get('compensation_amount', ''),
         request.form.get('post_url', ''),
         request.form.get('status', '進行中'), id]
    )
    db.commit()
    db.close()
    flash('コラボレーション情報を更新しました', 'success')
    return redirect(url_for('collaboration_list'))


@app.route('/collaborations/<int:id>/delete', methods=['POST'])
def collaboration_delete(id):
    db = get_db()
    db.execute('DELETE FROM collaborations WHERE id = ?', [id])
    db.commit()
    db.close()
    flash('コラボレーションを削除しました', 'info')
    return redirect(url_for('collaboration_list'))


# ─── 効果測定レポート ───
@app.route('/reports')
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

    # インフルエンサー別の集計
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
def report_add():
    db = get_db()
    db.execute(
        '''INSERT INTO collaboration_results
           (collaboration_id, views, likes, comments, new_followers,
            new_customers, revenue_impact, measured_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        [request.form['collaboration_id'],
         int(request.form.get('views') or 0),
         int(request.form.get('likes') or 0),
         int(request.form.get('comments') or 0),
         int(request.form.get('new_followers') or 0),
         int(request.form.get('new_customers') or 0),
         int(request.form.get('revenue_impact') or 0),
         request.form.get('measured_at') or None]
    )
    db.commit()
    db.close()
    flash('効果測定データを記録しました', 'success')
    return redirect(url_for('reports'))


@app.route('/reports/<int:id>/delete', methods=['POST'])
def report_delete(id):
    db = get_db()
    db.execute('DELETE FROM collaboration_results WHERE id = ?', [id])
    db.commit()
    db.close()
    flash('効果測定データを削除しました', 'info')
    return redirect(url_for('reports'))


# ─── API（Chart.js用） ───
@app.route('/api/report_data')
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
