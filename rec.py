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
import pyodbc
import numpy as np
import re
from scipy.signal import savgol_filter


conn = psycopg2.connect(database="roll_grinders",
                        user='postgres',
                        password='2378951',
                        host='localhost',
                        port=5432)



# коннект для mssql
server = 'MP-L-756R4M2\SQLEXPRESS'
database = 'SettingSql'
cnxn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';'
                                                                                            'trusted_connection=yes')
cursor = cnxn.cursor()



"""переменные для работой с шаблонизатором"""
templateLoader = jinja2.FileSystemLoader(searchpath="./")
templateEnv = jinja2.Environment(loader=templateLoader)

"""переменные абсолютных путей"""
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, 'report_templates')
fonts_dir = os.path.join(templates_dir, 'fonts')
font_arial_dir = os.path.join(fonts_dir, 'arial.ttf')

def get_list_of_max_val_every_few_val(l_val, divider):
	"""
	функция принимает на вход список и делитель.
	функция формирует матрицу из входного списка
	дробя его на количество элементов, указанных
	во втором аргументе. Затем функция возвращет
	список состоящий из максимальных значений
	каждого такого списка.
	"""
	count_iter = 0
	return_list = []
	temporary_list = []
	for i in range(len(l_val)):
		if count_iter == divider:
			return_list.append(max(temporary_list))
			temporary_list = []
			count_iter = 0
		else:
			temporary_list.append(l_val[i])
			count_iter += 1
			if i == len(l_val)-1:
				return_list.append(max(temporary_list))		
	return return_list


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
				BruiseBeforeGrinding = row[23]
				BruiseAfterGrinding =  row[24]
				CrackBeforeGrinding = row[25]
				CrackAfterGrinding = row[26]
				MagnetismBeforeGrinding = row[27]
				MagnetismAfterGrinding = row[28]
				CrackTreshold = row[29]
				BruiseTreshold = row[30]
				Operator = row[31]

				"""профиль"""
				shape_ref_val = [float(i) for i in shape_ref.split(',')]
				shape_after_grinding_val = [float(i) for i in shape_after_grinding.split(',')]

				"""отклонение"""
				deviation_after_grinding_val = [float(i) for i in deviation_after_grinding.split(',')]

				"""вихретоковая дефектоскопия"""
				BruiseAfterGrinding = np.array([float(i) for i in BruiseAfterGrinding.split(',')]) 
				BruiseAfterGrinding.resize((401, 360))
				y_BruiseAfterGrinding = np.amax(BruiseAfterGrinding, axis = 1)

				CrackAfterGrinding = np.array([float(i) for i in CrackAfterGrinding.split(',')]) 
				CrackAfterGrinding.resize((401, 360))
				y_CrackAfterGrinding = np.amax(CrackAfterGrinding, axis = 1)

				CrackBeforeGrinding = np.array([float(i) for i in CrackBeforeGrinding.split(',')]) 
				CrackBeforeGrinding.resize((401, 360))
				y_CrackBeforeGrinding = np.amax(CrackBeforeGrinding, axis = 1)

				MagnetismAfterGrinding = np.array([float(i) for i in MagnetismAfterGrinding.split(',')]) 
				MagnetismAfterGrinding.resize((401, 360))
				y_MagnetismAfterGrinding = np.amax(MagnetismAfterGrinding, axis = 1)

				step_val = [5.75*i for i in range(0, 401)]	# значения для всех графиков по оси y для профиля и отклонения и x для вихретоковой дефектоскопии

				
				"""построение графика по профилю"""
				fig_profile, ax_profile = plt.subplots()  # s образный график (профиль)
				ax_profile.plot(shape_ref_val, step_val, color='black', label='Заданная форма', linewidth = 0.5)
				ax_profile.plot([i+0.01 for i in shape_ref_val], step_val, color='red', label='Верхняя граница', linestyle='--', linewidth = 0.5)
				ax_profile.plot([i-0.01 for i in shape_ref_val], step_val, color='red', label='Нижняя граница', linestyle='--', linewidth = 0.5)
				ax_profile.plot(shape_after_grinding_val, step_val, color='blue', label='Фактическая кривая', linewidth = 0.5)
				ax_profile.margins(0)  # убрать отступы
				fig_profile.set_figwidth(6)  # задать ширину фигуры
				fig_profile.set_figheight(6)  # задать высоту фигуры
				fig_profile.gca().invert_yaxis()  # инвертировал ось y
				ax_profile.xaxis.tick_top()  # расположить ось x сверху
				ax_profile.set_xlabel("мм")  # подпись оси x
				ax_profile.xaxis.set_label_position('top')  # расположение надписи по оси x
				ax_profile.set_ylabel("мм")  # подпись оси у
				ax_profile.set_xlim(-0.01, 0.5)	 # ограничить ось по значениям
				plt.xticks(rotation=270) 
				ax_profile.xaxis.set_major_locator(ticker.MultipleLocator(0.05))  # дробление сетки для оси x
				ax_profile.yaxis.set_major_locator(ticker.MultipleLocator(100))  # дробление сетки для оси y
				ax_profile.grid(which='major', color = 'k', linestyle='--')
				plt.legend()  # bbox_to_anchor=(0.5, -0.1), loc='lower left')  #, ncol=2, mode="expand", borderaxespad=0.)

				"""сохранение изображения во временную память"""
				pic_IObytes = BytesIO()
				plt.savefig(pic_IObytes,  format='png')
				pic_IObytes.seek(0)
				profile_plot_image = b64encode(pic_IObytes.read()).decode('utf-8') # преобразование к base64 и декод в ютф-8

				"""построение графика по смещениям"""
				fig_shift, ax_shift = plt.subplots()
				ax_shift.plot(deviation_after_grinding_val, step_val, color='blue', label='Отклонение')
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
				plt.xticks(rotation=270)  # поворот надписей оси x
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


				
				#рисуем график
				"""построение графика по вихретоковой дефектоскопии после шлифования"""
				fig, ax = plt.subplots() 
				fig.set_figwidth(6) # задать ширину фигуры
				fig.set_figheight(7) # задать высоту фигуры
				ax.barh(step_val, y_BruiseAfterGrinding, height=7, color='yellow', label='Изменение структуры')
				ax.barh(step_val, y_CrackAfterGrinding, height=7, color='red', label='Риска')
				ax.barh(step_val, y_MagnetismAfterGrinding, height=7, color='blue', label='Магнетизм')
				ax.xaxis.tick_top()  # расположить ось x сверху
				ax.margins(0)  # убрать отступы
				fig.gca().invert_yaxis() # инвертировал ось y
				ax.set_xlim(0, 5000)  # ограничение оси x
				plt.xticks(rotation=270)  # поворот надписей оси x
				ax.set_xlabel("???")  # подпись оси x
				ax.xaxis.set_label_position('top')  # расположение надписи по оси x
				ax.xaxis.set_major_locator(ticker.MultipleLocator(200))
				ax.yaxis.set_major_locator(ticker.MultipleLocator(100))
				ax.grid(which='major', color = 'k', linestyle='--')
				plt.legend(loc='lower right')

				"""сохранение изображения во временную память"""
				pic_IObytes = BytesIO()
				plt.savefig(pic_IObytes,  format='png')
				pic_IObytes.seek(0)
				eddy_current_ag_plot_image = b64encode(pic_IObytes.read()).decode('utf-8') # преобразование к base64 и декод в ютф-8


				TEMPLATE_FILE = "report_templates/hercules_template.html"  # где хранится шаблон для отрисовки отчета
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
					operator=Operator,
					target_diameter=target_diameter,
					shape_ref_val=['%.3f'%val for val in shape_ref_val[::10]],
					shape_after_grinding_val=['%.3f'%val for val in shape_after_grinding_val[::10]],
					deviation_after_grinding_val=['%.3f'%val for val in deviation_after_grinding_val[::10]],
					BruiseAfterGrinding_val=[val for val in get_list_of_max_val_every_few_val(y_BruiseAfterGrinding, 9)],
					CrackAfterGrinding_val=[val for val in get_list_of_max_val_every_few_val(y_CrackAfterGrinding, 9)],
					MagnetismAfterGrinding_val=[val for val in get_list_of_max_val_every_few_val(y_MagnetismAfterGrinding, 9)],
					roll_diameter_before_grinding_head_stock=roll_diameter_before_grinding_head_stock, # перед бабк перед
					roll_diameter_after_grinding_head_stock=roll_diameter_after_grinding_head_stock, # перед бабк после
					roll_diameter_before_grinding_middle=roll_diameter_before_grinding_middle,
					roll_diameter_after_grinding_middle=roll_diameter_after_grinding_middle,
					roll_diameter_before_grinding_tail_stock=roll_diameter_before_grinding_tail_stock,
					roll_diameter_after_grinding_tail_stock=roll_diameter_after_grinding_tail_stock,
					profile_plot_image=profile_plot_image,
					shift_plot_image=shift_plot_image,
					eddy_current_ag_plot_image=eddy_current_ag_plot_image)

				outputFilename = f"pdf_reports/hercules/hercules_{name}.pdf"

				convertHtmlToPdf(outputText, outputFilename)



def get_report_pomini():
	#  здесь селект в бд
	FirstRealProFirstMap = '-0.8078994  -0.7891992  -0.7318301  -0.7129766  -0.6917822  -0.5651621  -0.6096611  -0.5873145  -0.5997734  -0.5458652  -0.4487324  -0.500791  -0.4463799  -0.4908477  -0.4624961  -0.4707354  -0.4419219  -0.4391572  -0.426083  -0.4243799  -0.4417822  -0.4259102  -0.4646289  -0.4377666  -0.4369268  -0.4472432  -0.4066357  -0.4423613  -0.4794863  -0.4778848  -0.4899678  -0.4737813  -0.5154326  -0.5128174  -0.5406543  -0.5169648  -0.5463711  -0.5151465  -0.5151123  -0.49404  -0.4968096  -0.5083652  -0.5056191  -0.5485898  -0.5764023  -0.5659521  -0.6052266  -0.5841318  -0.6217861  -0.6033457  -0.592417  -0.6249551  -0.6418877  -0.6361592  -0.642667  -0.6381152  -0.6703164  -0.6543184  -0.6673115  -0.6124775  -0.6018105  -0.5499609  -0.5760488  -0.5422578  -0.5398223  -0.516541  -0.5157793  -0.4855771  -0.4800898  -0.4429863  -0.4197363  -0.3954932  -0.3600156  -0.3466094  -0.3344062  -0.3123789  -0.284915  -0.2455977  -0.2269531  -0.1988027  -0.1311289  -0.1190146  -0.0686748  -0.04728711  0'
	FinalRealProFirstMap = '-0.8703965  -0.8304648  -0.7917217  -0.7583203  -0.726791  -0.6972207  -0.6678867  -0.6382744  -0.6165918  -0.5960117  -0.5768252  -0.5585322  -0.5402061  -0.5256699  -0.5129893  -0.4993301  -0.4905547  -0.4788623  -0.4701729  -0.4655205  -0.4582314  -0.4506729  -0.4484443  -0.4445264  -0.4427764  -0.440207  -0.4406152  -0.4438262  -0.4446113  -0.4474404  -0.4504434  -0.4533262  -0.4565283  -0.4601006  -0.4634004  -0.4674756  -0.4729473  -0.477749  -0.4821299  -0.4877471  -0.4952012  -0.503124  -0.5085234  -0.5137402  -0.5238457  -0.5273506  -0.5345752  -0.5425156  -0.5425635  -0.5494736  -0.5525957  -0.5537754  -0.5589609  -0.5625967  -0.5632725  -0.5669854  -0.5654648  -0.5689277  -0.5678516  -0.5638223  -0.5598242  -0.5559365  -0.5467646  -0.5396943  -0.5309404  -0.5175693  -0.5043066  -0.4945928  -0.4757637  -0.4596748  -0.4443096  -0.4242305  -0.4032783  -0.3818652  -0.355623  -0.3311855  -0.300417  -0.2719951  -0.2386504  -0.2066367  -0.1692783  -0.1302471  -0.09137012  -0.04533789  0'
	y_FirstRP = [float(i) for i in FirstRealProFirstMap.split('  ')]
	y_FinalRP = [float(i) for i in FinalRealProFirstMap.split('  ')]
	x_RealPro = [100+25*i for i in range(85)]
	# x_RealPro = [26.5*i for i in range(85)]

	# plot_image = get_plot_image_to_base64(x_values=x_RealPro, y_values_1=y_FirstRP, y_values_2=y_FinalRP,
	# 								 label_1='FirstRealPro', label_2='FinalRealPro', color_plot_1='r', color_plot_2='g')


	cursor.execute("""
	                select [First Realpro], [Final Realpro] from dbo.[Local Roll Data files]
	                where [Initial date/time] = ?
	                """, datetime.strptime('2020-05-08 11:58:35.00', '%Y-%m-%d %H:%M:%S.%f'))
	
	for row in cursor:
		row_to_list = [str(elem).replace('\r\n', ',') for elem in row]

	first_rp_first_map_start = row_to_list[0].find('Map')+5  # Находим map в строке и делаем отступ от него
	first_rp_first_map_end = [m.start() for m in re.finditer('Profile', row_to_list[0])][1]  # берем второе вхождение и делаем отступ
	first_rp_first_map = [float(val) for val in row_to_list[0][first_rp_first_map_start:first_rp_first_map_end].split(',')[:-1]]
	first_rp_second_map_start = [m.start() for m in re.finditer('Map', row_to_list[0])][1]+5  # берем второе вхождение Map и делаем отступ
	first_rp_second_map_finish = row_to_list[0].find('End') #print(second_map_start)
	first_rp_second_map = [float(val) for val in row_to_list[0][first_rp_second_map_start:first_rp_second_map_finish-1].split(',')[:-6]]
	
	final_rp_first_map_start = row_to_list[1].find('Map')+5  # Находим map в строке и делаем отступ от него
	final_rp_first_map_end = [m.start() for m in re.finditer('Profile', row_to_list[1])][1]  # берем второе вхождение и делаем отступ
	final_rp_first_map = [float(val) for val in row_to_list[1][final_rp_first_map_start:final_rp_first_map_end].split(',')[:-1]]
	final_rp_second_map_start = [m.start() for m in re.finditer('Map', row_to_list[1])][1]+5  # берем второе вхождение Map и делаем отступ
	final_rp_second_map_finish = row_to_list[1].find('End') #print(second_map_start)
	final_rp_second_map = [float(val) for val in row_to_list[1][final_rp_second_map_start:final_rp_second_map_finish-1].split(',')[:-6]]

	min_first_rp_first_map = min(first_rp_first_map)
	max_first_rp_first_map = max(first_rp_first_map)

	FinalTheoPro = '-1.028335  -1.00653  -0.985236  -0.964448  -0.9441605  -0.9243682  -0.9050658  -0.8862478  -0.867909  -0.8500439  -0.8326471  -0.8157134  -0.7992373  -0.7832135  -0.7676366  -0.7525013  -0.7378021  -0.7235337  -0.7096908  -0.6962679  -0.6832598  -0.670661  -0.6584662  -0.64667  -0.635267  -0.6242519  -0.6136193  -0.6033639  -0.5934802  -0.583963  -0.5748068  -0.5660062  -0.557556  -0.5494507  -0.541685  -0.5342536  -0.5271509  -0.5203718  -0.5139107  -0.5077624  -0.5019215  -0.4963826  -0.4911403  -0.4861893  -0.4815242  -0.4771397  -0.4730303  -0.4691908  -0.4656157  -0.4622997  -0.4592374  -0.4564234  -0.4538525  -0.4515191  -0.449418  -0.4475438  -0.445891  -0.4444545  -0.4432287  -0.4422083  -0.4413879  -0.4407623  -0.4403259  -0.4400736  -0.4399997  -0.4400992  -0.4403664  -0.4407961  -0.441383  -0.4421216  -0.4430066  -0.4440326  -0.4451942  -0.4464861  -0.447903  -0.4494393  -0.4510899  -0.4528493  -0.4547121  -0.4566731  -0.4587267  -0.4608677  -0.4630906  -0.4653902  -0.4677611  -0.4701978  -0.472695  -0.4752474  -0.4778496  -0.4804961  -0.4831818  -0.4859011  -0.4886487  -0.4914193  -0.4942075  -0.4970079  -0.4998151  -0.5026238  -0.5054287  -0.5082243  -0.5110053  -0.5137663  -0.5165019  -0.5192068  -0.5218757  -0.5245031  -0.5270837  -0.5296121  -0.532083  -0.5344909  -0.5368306  -0.5390966  -0.5412836  -0.5433862  -0.5453991  -0.5473169  -0.5491342  -0.5508456  -0.5524458  -0.5539295  -0.5552912  -0.5565255  -0.5576273  -0.5585909  -0.5594112  -0.5600826  -0.5606  -0.5609578  -0.5611507  -0.5611734  -0.5610205  -0.5606866  -0.5601663  -0.5594544  -0.5585453  -0.5574338  -0.5561145  -0.5545821  -0.5528311  -0.5508561  -0.5486519  -0.5462131  -0.5435342  -0.54061  -0.537435  -0.5340039  -0.5303114  -0.5263519  -0.5221203  -0.5176111  -0.512819  -0.5077385  -0.5023644  -0.4966912  -0.4907137  -0.4844263  -0.4778238  -0.4709008  -0.4636519  -0.4560718  -0.4481551  -0.4398964  -0.4312903  -0.4223316  -0.4130147  -0.4033345  -0.3932854  -0.3828621  -0.3720593  -0.3608716  -0.3492937  -0.33732  -0.3249454  -0.3121644  -0.2989717  -0.2853618  -0.2713295  -0.2568693  -0.241976  -0.226644  -0.2108681  -0.194643  -0.1779631  -0.1608232  -0.1432179  -0.1251418  -0.1065896  -0.08755587  -0.06803527  -0.04802244  -0.027512  -0.006498583  0.01502317  0.03705862  0.05961315  0.08269212  0.1063009  0.1304448  0.1551293  0.1803597  0.2061414'
	y_FinalTheoPro = [float(i) for i in FinalTheoPro.split('  ')]
	x_Theopro = [11.5*i for i in range(201)]

	cursor.execute("""
	                select
	                [Start date/time],
	                [Roll Nb],
	                [Profile code],
	                [Diam before head],
	                [Diam before mid],
	                [Diam before tail]
	                from dbo.[Roll Ground]
	                where [Start date/time] = ?
	                """, datetime.strptime('2020-05-08 11:58:35.00', '%Y-%m-%d %H:%M:%S.%f'))
	query = cursor.fetchall()
	start_date_time = query[0][0]
	roll_nb = query[0][1]
	profile_code = query[0][2]
	diam_before_head = query[0][3]
	diam_before_mid = query[0][4]
	diam_before_tail = query[0][5]
	


	cursor.execute("""
	                select
	                [Initial report],
	                [First Realpro date/time]
	                from dbo.[Local Roll Data files]
	                where [Initial date/time] = ?
	                """, datetime.strptime('2020-05-08 11:58:35.00', '%Y-%m-%d %H:%M:%S.%f'))
	cur_fetchall = cursor.fetchall()
	

	initial_report_values = str(cur_fetchall[0][0]).replace('\n', '').replace('\r', ',').split(',')
	operator_code = initial_report_values[17]
	machine_name = initial_report_values[20]
	machine_serial_number = initial_report_values[21]
	profile_tolerance = initial_report_values[30]
	taper_tolerance = initial_report_values[31]
	roll_lenght = initial_report_values[33]

	measurement_date = cur_fetchall[0][1]

	print(measurement_date)
	fig_profile, ax_profile = plt.subplots()
	fig_profile.set_figwidth(11) # задать ширину фигуры
	fig_profile.set_figheight(6) # задать высоту фигуры
	ax_profile.grid(which='major', color = 'gray')

	ax_profile.hlines(0, 0, 2300,
          color = 'black',
          linewidth = 1)

	ax_profile.plot(x_Theopro, [i+0.02 for i in y_FinalTheoPro], color='red', label='Граница допуска', linewidth = 1) # теоретический верхняя граница
	ax_profile.plot(x_Theopro, y_FinalTheoPro, color='red', label='Теоретический профиль', linewidth = 1, linestyle='--') # теоретический
	ax_profile.plot(x_Theopro, [i-0.02 for i in y_FinalTheoPro], color='red', linewidth = 1) # теоретический нижняя граница

	
	ax_profile.plot(x_RealPro, savgol_filter(first_rp_first_map, 3, 1), color='b', label='Реальный профиль (перед шлифовкой)', linewidth = 1)  # с фильтром
	# ax.plot(x_RealPro, first_rp_first_map, color='purple', label='FirstRealPro')  # без фильтра
	ax_profile.plot(x_RealPro, final_rp_first_map, color='black', label='Реальный профиль (после шлифовки)', linewidth = 1)  # профиль после шлифовки







	ax_profile.set_xlabel("Headstock <-- Millimetres --> Footstock")  # подпись оси x
	ax_profile.xaxis.set_label_position('bottom')  # расположение надписи по оси x
	ax_profile.set_ylabel("Millimetres")  # подпись оси y
	ax_profile.yaxis.set_label_position('right')  # расположение надписи по оси y
	ax_profile.xaxis.set_major_locator(ticker.MultipleLocator(460))  # дробление сетки для оси x
	ax_profile.margins(0)  # убрать отступы
	plt.legend(loc='lower right')

	"""сохранение изображения во временную память"""
	pic_IObytes = BytesIO()
	plt.savefig(pic_IObytes,  format='png')
	pic_IObytes.seek(0)
	first_plot_image = b64encode(pic_IObytes.read()).decode('utf-8') # преобразование к base64 и декод в ютф-8


	fig_profile, ax_profile = plt.subplots()
	fig_profile.set_figwidth(11) # задать ширину фигуры
	fig_profile.set_figheight(6) # задать высоту фигуры
	ax_profile.grid(which='major', color = 'gray')

	ax_profile.hlines(0, 0, 2300,
          color = 'black',
          linewidth = 1)


	ax_profile.set_xlabel("Headstock <-- Millimetres --> Footstock")  # подпись оси x
	ax_profile.xaxis.set_label_position('bottom')  # расположение надписи по оси x
	ax_profile.set_ylabel("Millimetres")  # подпись оси y
	ax_profile.yaxis.set_label_position('right')  # расположение надписи по оси y

	min_first_rp_second_map = min(first_rp_second_map)
	max_first_rp_second_map = max(first_rp_second_map)

	ax_profile.set_ylim(min_first_rp_second_map-0.01, max_first_rp_second_map+0.01)  # ограничение оси x


	ax_profile.plot(x_RealPro, first_rp_second_map, 'blue', label='?') 
	# ax_profile.plot(x_RealPro, savgol_filter(first_rp_second_map, 3, 1), 'r', label='') # первый график нижняя картинка
	# ax_profile.plot(x_RealPro, final_rp_second_map, 'red', label='') # не знаю что это
	# ax_profile.xaxis.set_major_locator(ticker.MultipleLocator(460))  # дробление сетки для оси x
	ax_profile.margins(0)  # убрать отступы
	plt.legend(loc='lower right')
	# plt.show()

	"""сохранение изображения во временную память"""
	pic_IObytes = BytesIO()
	plt.savefig(pic_IObytes,  format='png')
	pic_IObytes.seek(0)
	second_plot_image = b64encode(pic_IObytes.read()).decode('utf-8') # преобразование к base64 и декод в ютф-8

	TEMPLATE_FILE = "report_templates/pomini_template.html"  # где хранится шаблон для отрисовки отчета
	template = templateEnv.get_template(TEMPLATE_FILE)
	outputText = template.render(
		font_arial_dir=font_arial_dir,
		start_date_time=start_date_time,
		measurement_date=measurement_date,
		roll_nb=roll_nb,
		profile_code=profile_code,
		min_first_rp_first_map=min_first_rp_first_map,
		max_first_rp_first_map=max_first_rp_first_map,
		operator_code=operator_code,
		machine_serial_number=machine_serial_number,
		machine_name=machine_name,
		profile_tolerance=profile_tolerance,
		taper_tolerance=taper_tolerance,
		roll_lenght=roll_lenght,
		diam_before_head=diam_before_head,
		diam_before_mid=diam_before_mid,
		diam_before_tail=diam_before_tail,
		first_plot_image=first_plot_image,
		second_plot_image=second_plot_image)

	outputFilename = f"pdf_reports/pomini/pomini_119.pdf"

	convertHtmlToPdf(outputText, outputFilename)

	# print(str(row).replace(r"\r\n", ", "))


# get_report_hercules("466_07_05_2020_12_16_43", machine_num=6) 

get_report_pomini()

# def find_2nd(string, substring):
# 	return string.find(substring, string.find(substring) + 1)






