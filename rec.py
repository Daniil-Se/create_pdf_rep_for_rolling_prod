import os
from xhtml2pdf import pisa             
import matplotlib.pyplot as plt
import matplotlib.patheffects as mpe
from matplotlib import ticker
from base64 import b64encode
from io import BytesIO
import psycopg2
import jinja2
from datetime import datetime


conn = psycopg2.connect(database="roll_grinders",
                        user='postgres',
                        password='2378951',
                        host='localhost',
                        port=5432)


"""переменные для работой с шаблонизатором"""
templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)

"""переменные абсолютных путей"""
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, 'report_templates')
fonts_dir = os.path.join(templates_dir, 'fonts')
font_arial_dir = os.path.join(fonts_dir, 'arial.ttf')


def convertHtmlToPdf(sourceHtml, outputFilename):
    resultFile = open(outputFilename, "w+b")  # open output file for writing (truncated binary)
    pisaStatus = pisa.CreatePDF(sourceHtml, dest=resultFile, encoding='UTF-8')  # convert HTML to PDF
    resultFile.close()  # close output file
    return pisaStatus.err  # return True on success and False on errors


def get_report_hercules(file_name, machine_num): # в качестве агрументов передать номер геркулеса тк их два, в зависимости от этго будет другой импорт в бд и тд
	with conn:
		with conn.cursor() as cur:
			cur.execute("""SELECT * FROM test WHERE name = '{}'""".format(file_name))
			query = cur.fetchall()
			for row in query:
				
				name = row[1]
				description = row[2]
				measuring_lenght = row[3]
				program_no = row[4]
				start_grind_date = row[5] 
				end_grind_date = row[6]
				grinding_time = row[7]
				meas_off_set_head_stock = row[8]
				meas_off_set_tail_stock = row[9]
				shape_no = row[10]
				grind_id = row[11]
				form_tolerance = row[12]
				target_diameter = row[13]
				roll_diameter_before_grinding_head_stock = row[14]
				roll_diameter_after_grinding_head_stock = row[15]
				roll_diameter_before_grinding_middle = row[16]
				roll_diameter_after_grinding_middle = row[17]
				roll_diameter_before_grinding_tail_stock = row[18]
				roll_diameter_after_grinding_tail_stock = row[19]
				shape_ref = row[20]
				shape_after_grinding = row[21]
				deviation_after_grinding = row[22]
				bruise = row[23]
				crack =  row[24]
				magnetism = row[25]
				operator = row[26]

				shape_ref_val = [float(i) for i in shape_ref.split(',')]
				shape_after_grinding_val = [float(i) for i in shape_after_grinding.split(',')]
				deviation_after_grinding_val = [float(i) for i in deviation_after_grinding.split(',')]

				y_val = [5.75*i for i in range(0, 401)]	# значения для графиков по оси y
				fig_profile, ax_profile = plt.subplots() # s образный график (профиль)

				"""построение графика по профилю"""
				ax_profile.plot(shape_ref_val, y_val, color='black', label='Заданная форма', linewidth = 0.5)
				ax_profile.plot([i+0.01 for i in shape_ref_val], y_val, color='red', label='Верхняя граница', linestyle='--', linewidth = 0.5)
				ax_profile.plot([i-0.01 for i in shape_ref_val], y_val, color='red', label='Нижняя граница', linestyle='--', linewidth = 0.5)
				ax_profile.plot(shape_after_grinding_val, y_val, color='blue', label='Фактическая кривая', linewidth = 0.5)
				ax_profile.margins(0) # убрать отступы
				fig_profile.set_figwidth(6) # задать ширину фигуры
				fig_profile.set_figheight(6) # задать высоту фигуры
				fig_profile.gca().invert_yaxis() # инвертировал ось y
				ax_profile.xaxis.tick_top() # расположить ось x сверху
				ax_profile.set_xlabel("мм") # подпись оси x
				ax_profile.xaxis.set_label_position('top') # расположение надписи по оси x
				ax_profile.set_ylabel("мм") # подпись оси у
				ax_profile.set_xlim(-0.01, 0.5)	# ограничить ось по значениям
				plt.xticks(rotation=270) 
				ax_profile.xaxis.set_major_locator(ticker.MultipleLocator(0.05)) # дробление сетки для оси x
				ax_profile.yaxis.set_major_locator(ticker.MultipleLocator(100)) # дробление сетки для оси y
				ax_profile.grid(which='major', color = 'k', linestyle='--')
				plt.legend() #bbox_to_anchor=(0.5, -0.1), loc='lower left') #, ncol=2, mode="expand", borderaxespad=0.)

				"""сохранение изображения во временную память"""
				pic_IObytes = BytesIO()
				plt.savefig(pic_IObytes,  format='png')
				pic_IObytes.seek(0)
				profile_plot_image = b64encode(pic_IObytes.read()).decode('utf-8') # преобразование к base64 и декод в ютф-8

				"""построение графика по смещениям"""
				fig_shift, ax_shift = plt.subplots()
				ax_shift.plot(deviation_after_grinding_val, y_val, color='blue', label='Отклонение')
				ax_shift.plot(0.01, color='red')
				ax_shift.plot(-0.01, color='red')

				ax_shift.vlines(0.01, 0, 2300,
						          color = 'r',    #  цвет
						          linewidth = 1,    #  ширина
						          linestyle = '--',  #  начертание
						          label='Верхняя граница допуска')
				ax_shift.vlines(-0.01, 0, 2300,
						          color = 'r',    #  цвет
						          linewidth = 1,    #  ширина
						          linestyle = '--',  #  начертание
						          label='Нижняя граница допуска')    
				    
				"""построение графика по отклонению"""
				fig_shift.set_figwidth(6) # задать ширину фигуры
				fig_shift.set_figheight(7) # задать высоту фигуры
				fig_shift.gca().invert_yaxis() # инвертировал ось y
				ax_shift.xaxis.tick_top() # расположить ось x сверху
				ax_shift.set_xlabel("мм") # подпись оси x
				ax_shift.xaxis.set_label_position('top') # расположение надписи по оси x
				ax_shift.set_ylabel("мм") # подпись оси у
				ax_shift.set_xlim(-0.02, 0.02)	# ограничить ось по значениям
				plt.xticks(rotation=270)
				ax_shift.margins(0) # убрать отступы
				ax_shift.xaxis.set_major_locator(ticker.MultipleLocator(0.004))
				ax_shift.yaxis.set_major_locator(ticker.MultipleLocator(100))
				ax_shift.grid(which='major', color = 'k', linestyle='--')
				plt.legend(bbox_to_anchor=(-0.015, -0.15), loc='lower left')
				
				"""сохранение изображения во временную память"""
				pic_IObytes = BytesIO()
				plt.savefig(pic_IObytes,  format='png')
				pic_IObytes.seek(0)
				shift_plot_image = b64encode(pic_IObytes.read()).decode('utf-8') # преобразование к base64 и декод в ютф-8

				# plt.show() # показать графики

				TEMPLATE_FILE = "report_templates/hercules_template.html"
				template = templateEnv.get_template(TEMPLATE_FILE)

				outputText = template.render(
					font_arial_dir=font_arial_dir,
					name=name,
					machine_num=machine_num,
					date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
					end_grind_date=end_grind_date,
					description=description,
					program_no=program_no,
					measuring_lenght=measuring_lenght,
					grinding_time=grinding_time,
					shape_no=shape_no,
					grind_id=grind_id,
					meas_off_set_tail_stock=meas_off_set_tail_stock,
					meas_off_set_head_stock=meas_off_set_head_stock,
					form_tolerance=form_tolerance,
					operator=operator,
					target_diameter=target_diameter,
					shape_ref_val=['%.3f'%val for val in shape_ref_val[::10]],
					shape_after_grinding_val=['%.3f'%val for val in shape_after_grinding_val[::10]],
					deviation_after_grinding_val=['%.3f'%val for val in deviation_after_grinding_val[::10]],
					roll_diameter_before_grinding_head_stock=roll_diameter_before_grinding_head_stock, # перед бабк перед
					roll_diameter_after_grinding_head_stock=roll_diameter_after_grinding_head_stock, # перед бабк после
					roll_diameter_before_grinding_middle=roll_diameter_before_grinding_middle,
					roll_diameter_after_grinding_middle=roll_diameter_after_grinding_middle,
					roll_diameter_before_grinding_tail_stock=roll_diameter_before_grinding_tail_stock,
					roll_diameter_after_grinding_tail_stock=roll_diameter_after_grinding_tail_stock,
					profile_plot_image=profile_plot_image,
					shift_plot_image=shift_plot_image)

				outputFilename = f"pdf_reports/hercules/hercules_{name}.pdf"

				convertHtmlToPdf(outputText, outputFilename)



def get_report_pomini():
	# 	# здесь селект в бд
	FirstRealProFirstMap = '-0.8078994  -0.7891992  -0.7318301  -0.7129766  -0.6917822  -0.5651621  -0.6096611  -0.5873145  -0.5997734  -0.5458652  -0.4487324  -0.500791  -0.4463799  -0.4908477  -0.4624961  -0.4707354  -0.4419219  -0.4391572  -0.426083  -0.4243799  -0.4417822  -0.4259102  -0.4646289  -0.4377666  -0.4369268  -0.4472432  -0.4066357  -0.4423613  -0.4794863  -0.4778848  -0.4899678  -0.4737813  -0.5154326  -0.5128174  -0.5406543  -0.5169648  -0.5463711  -0.5151465  -0.5151123  -0.49404  -0.4968096  -0.5083652  -0.5056191  -0.5485898  -0.5764023  -0.5659521  -0.6052266  -0.5841318  -0.6217861  -0.6033457  -0.592417  -0.6249551  -0.6418877  -0.6361592  -0.642667  -0.6381152  -0.6703164  -0.6543184  -0.6673115  -0.6124775  -0.6018105  -0.5499609  -0.5760488  -0.5422578  -0.5398223  -0.516541  -0.5157793  -0.4855771  -0.4800898  -0.4429863  -0.4197363  -0.3954932  -0.3600156  -0.3466094  -0.3344062  -0.3123789  -0.284915  -0.2455977  -0.2269531  -0.1988027  -0.1311289  -0.1190146  -0.0686748  -0.04728711  0'
	FinalRealProFirstMap = '-0.8703965  -0.8304648  -0.7917217  -0.7583203  -0.726791  -0.6972207  -0.6678867  -0.6382744  -0.6165918  -0.5960117  -0.5768252  -0.5585322  -0.5402061  -0.5256699  -0.5129893  -0.4993301  -0.4905547  -0.4788623  -0.4701729  -0.4655205  -0.4582314  -0.4506729  -0.4484443  -0.4445264  -0.4427764  -0.440207  -0.4406152  -0.4438262  -0.4446113  -0.4474404  -0.4504434  -0.4533262  -0.4565283  -0.4601006  -0.4634004  -0.4674756  -0.4729473  -0.477749  -0.4821299  -0.4877471  -0.4952012  -0.503124  -0.5085234  -0.5137402  -0.5238457  -0.5273506  -0.5345752  -0.5425156  -0.5425635  -0.5494736  -0.5525957  -0.5537754  -0.5589609  -0.5625967  -0.5632725  -0.5669854  -0.5654648  -0.5689277  -0.5678516  -0.5638223  -0.5598242  -0.5559365  -0.5467646  -0.5396943  -0.5309404  -0.5175693  -0.5043066  -0.4945928  -0.4757637  -0.4596748  -0.4443096  -0.4242305  -0.4032783  -0.3818652  -0.355623  -0.3311855  -0.300417  -0.2719951  -0.2386504  -0.2066367  -0.1692783  -0.1302471  -0.09137012  -0.04533789  0'
	y_FirstRP = [float(i) for i in FirstRealProFirstMap.split('  ')]
	y_FinalRP = [float(i) for i in FinalRealProFirstMap.split('  ')]
	x_RealPro = [27*i for i in range(85)]

	plot_image = get_plot_image_to_base64(x_values=x_RealPro, y_values_1=y_FirstRP, y_values_2=y_FinalRP,
									 label_1='FirstRealPro', label_2='FinalRealPro', color_plot_1='r', color_plot_2='g')


	
	TEMPLATE_FILE = "hercules_template.html"
	template = templateEnv.get_template(TEMPLATE_FILE)
	outputText = template.render(name='Mark', plot_image=plot_image)
	outputFilename = "hercules_report.pdf"
	convertHtmlToPdf(outputText, outputFilename)


# get_report_pomini()
get_report_hercules("466_07_05_2020_12_16_43", machine_num=6)










