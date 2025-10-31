from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simple_waste.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


class WasteRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(100), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)
    food_prepared = db.Column(db.Float, nullable=False)
    food_served = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def food_wasted(self):
        return self.food_prepared - self.food_served
    
    @property
    def waste_percentage(self):
        if self.food_prepared > 0:
            return (self.food_wasted / self.food_prepared) * 100
        return 0


@app.route('/')
def home():
    records = WasteRecord.query.order_by(WasteRecord.date.desc()).limit(10).all()
    

    total_records = WasteRecord.query.count()
    total_wasted = sum(r.food_wasted for r in WasteRecord.query.all())
    total_prepared = sum(r.food_prepared for r in WasteRecord.query.all())
    avg_waste = (total_wasted / total_prepared * 100) if total_prepared > 0 else 0
    
    return render_template('home.html', 
                         records=records,
                         total_records=total_records,
                         total_wasted=total_wasted,
                         avg_waste=avg_waste)

@app.route('/add', methods=['GET', 'POST'])
def add_record():
    if request.method == 'POST':
        record = WasteRecord(
            school_name=request.form['school_name'],
            meal_type=request.form['meal_type'],
            food_prepared=float(request.form['food_prepared']),
            food_served=float(request.form['food_served']),
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        )
        
        db.session.add(record)
        db.session.commit()
        flash('Registro adicionado com sucesso!', 'success')
        return redirect(url_for('home'))
    
    return render_template('add.html')

@app.route('/delete/<int:id>', methods=['POST'])
def delete_record(id):
    record = WasteRecord.query.get_or_404(id)
    db.session.delete(record)
    db.session.commit()
    flash('Registro deletado com sucesso!', 'success')
    return redirect(url_for('reports'))

@app.route('/reports')
def reports():
    records = WasteRecord.query.order_by(WasteRecord.date.desc()).all()
    

    chart_data = []
    for record in records[-7:]:  
        chart_data.append({
            'date': record.date.strftime('%d/%m'),
            'waste': float(record.food_wasted)
        })
    
    return render_template('reports.html', 
                         records=records,
                         chart_data=json.dumps(chart_data))

@app.before_request
def create_tables():
    db.create_all()
    

    if WasteRecord.query.count() == 0:
        sample_data = [
            WasteRecord(school_name='Escola Municipal Centro', meal_type='lunch', 
                       food_prepared=50.0, food_served=45.0, date=date.today()),
            WasteRecord(school_name='Colégio Estadual Norte', meal_type='breakfast', 
                       food_prepared=30.0, food_served=28.0, date=date.today()),
            WasteRecord(school_name='EMEF Sul', meal_type='lunch', 
                       food_prepared=40.0, food_served=35.0, date=date.today())
        ]
        
        for record in sample_data:
            db.session.add(record)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
