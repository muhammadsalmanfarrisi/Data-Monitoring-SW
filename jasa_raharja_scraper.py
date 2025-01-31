from flask import Flask, render_template, request
from datetime import datetime
from calendar import monthrange
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import time


app = Flask(__name__)

MAX_THREADS = 5
current_year = datetime.now().year
previous_year = current_year - 1
# Fungsi untuk mengambil data dari URL dengan cookies
def ambil_data(url, retries=3, timeout=10):
    # Membuat session untuk mengelola cookies
    session = requests.Session()

    # Menambahkan cookies yang Anda salin dari browser (Ganti dengan cookies yang relevan)
    cookies = {
        'XSRF-TOKEN': 'eyJpdiI6IlRFVVRiUUwyR0JBRk1tdEdDWVRxZ3c9PSIsInZhbHVlIjoiNGdUNG5oR0ZpcnBjeC9ka2JoMjNVb2dvSGxRVjRxQkxvL0k5M0VhclNOcE91eTZScHk2MUNQcytOckdITWxSMkJFK2F2SGNrY2dHZk9SdjdwV3hiWmUwOW5PaXdpditYbXU0bU12WStpZlF3WUxYMTdNc1daaVc2L2lwOG8yZE0iLCJtYWMiOiI2NzljYTM2NTFkOTQ0ZDI4N2EyMTdiZWE2ZWMxZDBlNGMzZGYzNjI1MTA1ZGNlZjIzYjdhOWQ2OTAwZTVmZGI3IiwidGFnIjoiIn0%3D',
        '_ga': 'GA1.1.140722331.1727057868',
        '_ga_JQ088T32QP': 'GS1.1.1727061610.2.1.1727061629.0.0.0', 
        '_ga_VNWN27RPNX': 'GS1.3.1727061611.2.0.1727061611.60.0.0', 
        'ceri_session': 'eyJpdiI6ImRTT2s5bWlGdzVNWmhMVkFnUVU0VlE9PSIsInZhbHVlIjoiSTFCa0NOcTZVN2RjVXRFSnNhc2ZoV3hWTzZxZW1JTFRpS21sUnJ6UldLaitLV1NjR0VkOWE1SENEbEkyTlg5TVUrSDV3TldNclBFbDJ2VEtpblZTZyt3S3M1eEt6bzJ1eG9raWJtVVlKclIyRCs0WFN2VklLU1JmbURISkt6Z1ciLCJtYWMiOiI0M2ZlMDhjNGJiOGUzOWM5MzU5YzJhOTFhOTAyYTc5MmY2MDU3YTEzMjQ4ZjU1N2U1MjVjZjU0OGFmNDhjZjYxIiwidGFnIjoiIn0%3D',
        'cookiesession1': '678B28C4BA1B09254D21278D87A606A5',
        'jr_cookie': 'c686aabd2eea2ae0eedde6ce6a909c67',
        'remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d': 'eyJpdiI6Ii9wYUR3Qm9aNFh0WEhOUjQ5K2FYbXc9PSIsInZhbHVlIjoiRXVTWkZQNThZTWFoZ0ZBQU41SE1obFVQK0pncW0rQ3EwRHdQbkp0MGE1QmtWZXBxSnAveWNsQ2h3ZzNjWVZXV0pHVUlJNGs3dm1oZTlNSHVGVGRCU0VOK1E3QUVaaS9yNHpPR09abGx3VmZoSVF6dWFJbk51NEZ3eXdHODNwcjRVbXZ1cFRCL0xKdkFYaUxiTTdTSWVRPT0iLCJtYWMiOiJkN2NkMzQ5Mjc3NTVhYmRiNzU4NzBiNmU4MjE2NWQ5NzgwNDE5NWNjYWI2YTFkZTY1MDQxMjAxYjZlMGFkYmEwIiwidGFnIjoiIn0%3D'
    }

    # Update session dengan cookies
    session.cookies.update(cookies)

    # Header User-Agent untuk mensimulasikan permintaan dari browser (Google Chrome)
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
    }

    try:
        # Kirim permintaan GET
        response = session.get(url, headers=headers)
        
        if response.status_code == 200:
            try:
                # Coba parsing JSON dari response
                data = response.json()
                result = []
                total_jml_sw = 0
                
                # Iterasi setiap item dalam data['data']
                for item in data['data']:
                    try:
                        # Pastikan 'jml_sw' adalah float
                        jml_sw = float(item['jml_sw'])
                    except (ValueError, TypeError):
                        # Jika tidak bisa dikonversi, set nilai default 0.0
                        jml_sw = 0.0
                    
                    # Tambahkan item ke dalam list result
                    result.append({
                        'kantor_jr': item['kantor_jr'],
                        'jml_sw': jml_sw,
                        'kode_kantor_jr': item['kode_kantor_jr']  # Menambahkan kode_kantor_jr
                    })
                    
                    # Tambahkan nilai jml_sw ke total_jml_sw
                    total_jml_sw += jml_sw

                # Kembalikan hasil dan total
                return result, total_jml_sw
            except ValueError:
                # Tangani jika response tidak dalam format JSON
                print("Response tidak dalam format JSON")
                return None, None
        else:
            # Tangani jika status code bukan 200
            print(f"Error: {response.status_code}")
            return None, None
    except requests.exceptions.RequestException as e:
        # Tangani jika ada error saat melakukan request
        print(f"Request Error: {e}")
        return None, None


# Fungsi untuk menghitung total jml_sw per bulan secara paralel
def ambil_total_bulanan_paralel(tahun):
    with ThreadPoolExecutor() as executor:
        futures = []
        for bulan in range(1, 13):
            start_date = f"01-{bulan:02d}-{tahun}"
            end_day = monthrange(tahun, bulan)[1]  # Mendapatkan tanggal akhir yang tepat untuk bulan tersebut
            end_date = f"{end_day}-{bulan:02d}-{tahun}"
            
            url = f'https://ceri.jasaraharja.co.id/monitoring/swdkllj/datatables/{start_date}_{end_date}_0400001_1?_=1733116412480'
            futures.append(executor.submit(ambil_data, url))  # Menjalankan ambil_data secara paralel
        
        # Mengambil hasil secara paralel
        bulanan_totals = []
        total_jml_sw_all_years = 0
        for future in futures:
            result, total_jml_sw = future.result()
            bulanan_totals.append(total_jml_sw if total_jml_sw is not None else 0)
            total_jml_sw_all_years += total_jml_sw
        
        return bulanan_totals, total_jml_sw_all_years
    
def ambil_total_bulanan_paralel_purwokerto(tahun):
    with ThreadPoolExecutor() as executor:
        futures = []
        for bulan in range(1, 13):
            start_date = f"01-{bulan:02d}-{tahun}"
            end_day = monthrange(tahun, bulan)[1]  # Mendapatkan tanggal akhir yang tepat untuk bulan tersebut
            end_date = f"{end_day}-{bulan:02d}-{tahun}"
            
            url = f'https://ceri.jasaraharja.co.id/monitoring/swdkllj/datatables/{start_date}_{end_date}_0400300_2?_=1731895548035'
            futures.append(executor.submit(ambil_data, url))  # Menjalankan ambil_data secara paralel
        
        # Mengambil hasil secara paralel
        bulanan_totals_purwokerto = []
        total_jml_sw_all_years_purwokerto = 0
        for future in futures:
            result, total_jml_sw = future.result()
            bulanan_totals_purwokerto.append(total_jml_sw if total_jml_sw is not None else 0)
            total_jml_sw_all_years_purwokerto += total_jml_sw
        
        return bulanan_totals_purwokerto, total_jml_sw_all_years_purwokerto

def gabungkan_data_per_kantor(data_2023, data_2024):
    # Dictionary untuk menyimpan data per kantor
    data_kantor = {}

    # Proses data 2023
    for item in data_2023:
        kode_kantor = item['kode_kantor_jr']
        if kode_kantor not in data_kantor:
            data_kantor[kode_kantor] = {
                'kode_kantor_jr': kode_kantor,
                'kantor_jr': item['kantor_jr'],
                'total_sw_2023': item['jml_sw'],
                'total_sw_2024': 0  # Inisialisasi untuk 2024
            }
        else:
            data_kantor[kode_kantor]['total_sw_2023'] += item['jml_sw']

    # Proses data 2024
    for item in data_2024:
        kode_kantor = item['kode_kantor_jr']
        if kode_kantor not in data_kantor:
            data_kantor[kode_kantor] = {
                'kode_kantor_jr': kode_kantor,
                'kantor_jr': item['kantor_jr'],
                'total_sw_2023': 0,  # Inisialisasi untuk 2023
                'total_sw_2024': item['jml_sw']
            }
        else:
            data_kantor[kode_kantor]['total_sw_2024'] += item['jml_sw']

    # Ubah dictionary ke list untuk digunakan di template
    return list(data_kantor.values())

@app.route('/', methods=['GET', 'POST'])
def index():
    
    # Ambil total bulanan dan tahunan
    bulanan_2023, total_2023 = ambil_total_bulanan_paralel(previous_year)
    bulanan_2024, total_2024 = ambil_total_bulanan_paralel(current_year)

    # Inisialisasi data kantor
    data_kantor = []

    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'form1':
            # Mendapatkan tanggal mulai dan akhir untuk dua rentang (2023 dan 2024)
            start_date_2023 = request.form['start_date_2023']
            end_date_2023 = request.form['end_date_2023']
            start_date_2024 = request.form['start_date_2024']
            end_date_2024 = request.form['end_date_2024']

            # URL API untuk data 2023 dan 2024
            url_2023 = f'https://ceri.jasaraharja.co.id/monitoring/swdkllj/datatables/{start_date_2023}_{end_date_2023}_0400001_1?_=1731895548035'
            url_2024 = f'https://ceri.jasaraharja.co.id/monitoring/swdkllj/datatables/{start_date_2024}_{end_date_2024}_0400001_1?_=1731895548035'

            # Ambil data API
            data_2023, total_jml_sw_2023 = ambil_data(url_2023)
            data_2024, total_jml_sw_2024 = ambil_data(url_2024)

            # Gabungkan data per kantor
            data_kantor = gabungkan_data_per_kantor(data_2023, data_2024)

            return render_template('index.html', data_2023=data_2023, data_2024=data_2024,data_kantor=data_kantor, total_jml_sw_2023=total_jml_sw_2023,
                                   total_jml_sw_2024=total_jml_sw_2024, start_date_2023=start_date_2023,
                                   end_date_2023=end_date_2023, start_date_2024=start_date_2024, 
                                   end_date_2024=end_date_2024, bulanan_2023=bulanan_2023, total_2023=total_2023, current_year=current_year, previous_year=previous_year,
                                   bulanan_2024=bulanan_2024, total_2024=total_2024)

    return render_template('index.html', data_kantor=data_kantor, data_2023=None, data_2024=None, 
                           bulanan_2023=bulanan_2023, total_2023=total_2023, bulanan_2024=bulanan_2024, current_year=current_year, previous_year=previous_year, total_2024=total_2024)


@app.route('/halaman_tertuju/<kode_kantor_jr>', methods=['GET', 'POST'])
def halaman_tertuju(kode_kantor_jr):
    kantor_jr_query = request.args.get('kantor_jr', kode_kantor_jr)
    # Mendapatkan tanggal mulai dan akhir untuk dua rentang (2023 dan 2024)
    start_date_2023 = request.form.get('start_date_2023', '2023-01-01')
    end_date_2023 = request.form.get('end_date_2023', '2023-12-31')
    start_date_2024 = request.form.get('start_date_2024', '2024-01-01')
    end_date_2024 = request.form.get('end_date_2024', '2024-12-31')

    # URL API untuk data 2023 dan 2024 dengan kode_kantor_jr
    url_2023 = f'https://ceri.jasaraharja.co.id/monitoring/swdkllj/datatables/{start_date_2023}_{end_date_2023}_{kode_kantor_jr}_2?_=1731895548035'
    url_2024 = f'https://ceri.jasaraharja.co.id/monitoring/swdkllj/datatables/{start_date_2024}_{end_date_2024}_{kode_kantor_jr}_2?_=1731895548035'

    # Ambil data API untuk 2023 dan 2024
    data_2023, total_jml_sw_2023 = ambil_data(url_2023)
    data_2024, total_jml_sw_2024 = ambil_data(url_2024)

    # Gabungkan data per kantor
    data_kantor = gabungkan_data_per_kantor(data_2023, data_2024)

    # Menghitung perbedaan dan perubahan persentase
    diff = total_jml_sw_2024 - total_jml_sw_2023
    percent_change = (diff / total_jml_sw_2023) * 100 if total_jml_sw_2023 != 0 else 0

    return render_template('halaman_tertuju.html',
                           data_kantor=data_kantor,
                           total_jml_sw_2023=total_jml_sw_2023,
                           total_jml_sw_2024=total_jml_sw_2024,
                           start_date_2023=start_date_2023,
                           end_date_2023=end_date_2023,
                           start_date_2024=start_date_2024,
                           end_date_2024=end_date_2024,
                           diff=diff, current_year=current_year, previous_year=previous_year,
                           percent_change=percent_change, kantor_jr=kantor_jr_query)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5555)