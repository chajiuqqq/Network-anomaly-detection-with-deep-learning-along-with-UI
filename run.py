from PyQt5.Qt import *
import ui2 as ui2
import sys
import multiprocessing as mp
import title as title
import UI.cut_pcap as cut_pcap
import dataprocess.datasave as datasave
import predict_c_2 as predict
import pandas as pd

class PredictEntity:
    def getshowdata(self,):
        data_csv_data = pd.read_csv(r"./data/show_data.csv", encoding='gbk', parse_dates=True)
        data_csv_label = pd.read_csv(r"./data/show_label.csv", encoding='gbk', parse_dates=True)
        length = len(data_csv_label) - (data_csv_data['flowmember'].max() - (data_csv_data['flowmember'].max() //64) *64)
        k=(data_csv_data['flowmember'].max() //64) *64
        for i in range(length, len(data_csv_label)):
            data_csv_label['label'][k] = data_csv_label['label'][i]
            data_csv_label['classes'][k] = data_csv_label['classes'][i]
            k+= 1
        j = 1
        i = 0
        count = 0
        while i < len(data_csv_data):
            if data_csv_data['flowmember'][i] == j:
                data_csv_data['label'][i] = data_csv_label['label'][j-1]
                data_csv_data['classes'][i]=data_csv_label['classes'][j-1]
                i += 1
            else:
                j = j + 1
                #         print("i",i)
                if j > data_csv_data['flowmember'].max():
                    break
                data_csv_data['label'][i] = data_csv_label['label'][j-1]
                data_csv_data['classes'][i] = data_csv_label['classes'][j-1]
                i += 1
        return data_csv_data

    def curtail_pcap(self,):
        print('正在执行捕捉，请稍等')
        num_cores = int(mp.cpu_count())
        pool = mp.Pool(num_cores)
        moder = cut_pcap.pcap_cut()  # 继承截取pcap的类,传入
        clip_num = 400  #截取数据包的数量
        # moder.read_pcap2('benign.csv',pool)
        self.data = moder.read_pcap2('save.pkl', pool,clip_num) # 获得pcap提取的流量包的数据
        print('截取成功!保存五元组和数据部分为save.pkl和save.csv')
        data_save=datasave.savedata(self.data,filename="test_data")
        data_save.save_excel()
        print('并按照数据流划分保存到NetData/testdata下')
        print('导出为/dataprocess/test_data.csv')

    def startdetection(self):
        print('正在预测，请稍等')
        path = r'./test_data.csv'
        predicted=predict.predict(path)
        predicted.finallmainmodel1()
        predicted.finallmainmodel2()
        predicted.finallmainmodel3()
        predicted.statistic()
        data_csv_data=self.getshowdata()
        print('保存/data/shown.csv,特征包括data，flowmember，label，classes')
        self.saveshowdata(data_csv_data)
        data_orginal = pd.read_pickle(r"save.pkl")

        data_show = pd.read_csv(r"./data/shown.csv", encoding='gbk', parse_dates=True)
        data_orginal['label'] = 0
        data_orginal['classes']=0
        data_orginal=self.finalldata(data_orginal,data_show)
        
        print('保存/data/shown_finall.csv，显示每个数据包的五元组，data，预测类别')
        self.savelabelshown(data_orginal)

        print('分析预测结果：')
        self.studyPredictResult('./data/shown_finall.csv')


    def saveshowdata(self,data_csv_data):
        import xlwt
        # 创建一个workbook 设置编码
        workbook = xlwt.Workbook(encoding='utf-8')
        # 创建一个worksheet
        worksheet = workbook.add_sheet('My Worksheet')
        worksheet.write(0,0,label='data')
        worksheet.write(0,1,label='flowmember')
        worksheet.write(0,2,label='label')
        worksheet.write(0,3,label='classes')
        for i in range(len(data_csv_data)):
            worksheet.write(i + 1, 0, label=str(data_csv_data['data'][i]))
            worksheet.write(i + 1, 1, label=str(data_csv_data['flowmember'][i]))
            worksheet.write(i + 1, 2, label=str(data_csv_data['label'][i]))
            worksheet.write(i + 1, 3, label=str(data_csv_data['classes'][i]))
        workbook.save('./data/shown.csv')
        data = pd.read_excel('./data/shown.csv', index_col=0)
        data.to_csv('./data/shown.csv', encoding='utf-8')

    def finalldata(self,data_orginal, data_show):
        for i in range(len(data_orginal)):
            for j in range(len(data_show)):
                if data_orginal['data'][i] == data_show['data'][j]:
                    data_orginal['label'][i]=data_show['label'][j]
                    data_orginal['classes'][i]=data_show['classes'][j]
        return data_orginal

    def savelabelshown(self,data_orginal):
        import xlwt
        # 创建一个workbook 设置编码
        workbook = xlwt.Workbook(encoding='utf-8')
        # 创建一个worksheet
        worksheet = workbook.add_sheet('My Worksheet')
        worksheet.write(0, 0, label='srcip')
        worksheet.write(0, 1, label='dstip')
        worksheet.write(0, 2, label='sport')
        worksheet.write(0, 3, label='dport')
        worksheet.write(0, 4, label='proto')
        worksheet.write(0, 5, label='data')
        worksheet.write(0, 6, label='label')
        worksheet.write(0, 7, label='classes')
        for i in range(len(data_orginal)):
            worksheet.write(i+1,0, label=str(data_orginal['srcip'][i]))
            worksheet.write(i+1,1, label=str(data_orginal['dstip'][i]))
            worksheet.write(i+1,2, label=str(data_orginal['sport'][i]))
            worksheet.write(i+1,3, label=str(data_orginal['dport'][i]))
            worksheet.write(i+1,4, label=str(data_orginal['proto'][i]))
            worksheet.write(i+1,5, label=str(data_orginal['data'][i]))
            worksheet.write(i+1,6, label=str(data_orginal['label'][i]))
            worksheet.write(i+1,7, label=str(data_orginal['classes'][i]))
        workbook.save('./data/shown_finall.csv')
        data = pd.read_excel('./data/shown_finall.csv', index_col=0)
        data.to_csv('./data/shown_finall.csv', encoding='utf-8')

    def studyPredictResult(self,filename):
        data = pd.read_csv(filename, index_col=0)
        data_abnormal = data[data['label']==1]
        print('异常数据包数量：',len(data_abnormal),'，已导出为data_abnormal.csv')
        data_abnormal.to_csv('./data/data_abnormal.csv', encoding='utf-8')


        # data_abnormal_distinct = data_abnormal.drop_duplicates(subset=['srcip','dstip','sport','dport','proto'])
        # data_abnormal_distinct.to_csv('./data/data_abnormal_distinct.csv', encoding='utf-8')
        # print('异常源数量：',len(data_abnormal_distinct))


if __name__ == '__main__':
    p = PredictEntity()
    while True:
        a = int(input('1:capture,2:predict'))
        if a == 1:
            p.curtail_pcap()
        if a == 2:
            p.startdetection()
                
