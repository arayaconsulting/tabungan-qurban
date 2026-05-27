from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'kunci_rahasia_araya_123')

# Database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qurban.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model Data
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(20), nullable=False)
    target_harga = db.Column(db.Integer, default=3500000)
    setoran = db.relationship('Setoran', backref='penabung', lazy=True)

class Setoran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nominal = db.Column(db.Integer, nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')

with app.app_context():
    db.create_all()
    if not User.query.first():
        sample_user = User(nama="Ali Mahfud", whatsapp="08123456789", target_harga=3500000)
        db.session.add(sample_user)
        db.session.commit()

@app.route('/')
def index():
    user = User.query.get(1)
    total_tertabung = sum(s.nominal for s in user.setoran if s.status == 'Disetujui')
    persentase = min(int((total_tertabung / user.target_harga) * 100), 100) if user.target_harga > 0 else 0
    sisa_bayar = max(user.target_harga - total_tertabung, 0)
    return render_template('dashboard.html', user=user, total=total_tertabung, persen=persentase, sisa=sisa_bayar)

@app.route('/setor', methods=['POST'])
def setor_dana():
    nominal = request.form.get('nominal')
    if nominal and int(nominal) > 0:
        baru_setoran = Setoran(user_id=1, nominal=int(nominal), status='Pending')
        db.session.add(baru_setoran)
        db.session.commit()
        flash('Laporan setoran berhasil terkirim! Menunggu konfirmasi bendahara.', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_panel():
    semua_setoran = Setoran.query.order_by(Setoran.id.desc()).all()
    return render_template('admin.html', setorans=semua_setoran)

@app.route('/admin/verifikasi/<int:id>/<string:status_baru>')
def verifikasi(id, status_baru):
    transaksi = Setoran.query.get(id)
    if transaksi and status_baru in ['Disetujui', 'Ditolak']:
        transaksi.status = status_baru
        db.session.commit()
        flash(f'Transaksi ID #{id} berhasil diperbarui.', 'info')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
