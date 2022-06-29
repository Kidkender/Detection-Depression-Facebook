#pip install pyqt5designer
#pip install pyqt5 tools 
#pyuic5 Gui.ui -o Gui.py

import pickle
from keras.models import load_model
import sys
from PyQt5.QtWidgets import QApplication,QMainWindow,QMessageBox,QHeaderView,QDialog,QAbstractScrollArea
from PyQt5 import QtCore
from Gui import Ui_Dialog
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from datetime import datetime,timedelta
import pandas as pd
import numpy as np

url = 'https://www.facebook.com'
s = Service(r"chromedriver.exe")
driver = webdriver.Chrome(service=s)
driver.get(url)
Qt = QtCore.Qt

model_ANN = load_model("Sentiment-ANN.h5")
model_KNN = pickle.load(open("Sentiment-knn.pickle", 'rb'))
model_BNB = pickle.load(open("Sentiment-BNB.pickle", 'rb'))
model_LR = pickle.load(open("Sentiment-LR.pickle", 'rb'))
model_RF = pickle.load(open("Sentiment-RandomF.pickle", 'rb'))

model_ANN_time = load_model("model_ann_time.h5")
model_KNN_time = pickle.load(open("model_knn_time.pickle", 'rb'))
model_BNB_time = pickle.load(open("model_bayes_time.pickle", 'rb'))
model_LR_time = pickle.load(open("model_regress_time.pickle", 'rb'))
model_RF_time = pickle.load(open("model_RF_time.pickle", 'rb'))

tranfrom = pickle.load(open("tranfrom_text.pkl", 'rb'))

model = [model_ANN,model_KNN,model_BNB,model_LR,model_RF]
model_time = [model_ANN_time,model_KNN_time,model_BNB_time,model_LR_time,model_RF_time]

class PandasModel(QtCore.QAbstractTableModel):
    def __init__(self, data, parent=None):
        QtCore.QAbstractTableModel.__init__(self, parent)
        self._data = data

    def rowCount(self, parent=None):
        return len(self._data.values)

    def columnCount(self, parent=None):
        return self._data.columns.size

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return QtCore.QVariant(str(
                    self._data.iloc[index.row()][index.column()]))
        return QtCore.QVariant()
    
    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col]
        return None

class MainWindow(QDialog):
    def __init__(self):
        super(MainWindow,self).__init__()
        self.main_win = QMainWindow()
        self.uic = Ui_Dialog()
        self.uic.setupUi(self.main_win)
        self.uic.btnGetData.clicked.connect(self.GetData)
        self.uic.btnDuDoan.clicked.connect(self.Predict)
        self.Links = []
        self.Status = []
        self.Comment = []
        self.Times = []
        self.df = None
        
    def Predict(self):
            _model = model[int(self.uic.cb_Model.currentIndex())]
            _model_time = model_time[int(self.uic.cb_Model.currentIndex())]
            print(self.Times)
            print(self.Status)
            print(self.Comment)
            text = self.Status
            text = tranfrom.transform(text)
            predict_status = _model.predict(text)
        
            timess = [np.array([int(x),100]) for x in self.Times]
            timess = np.array(timess).reshape(len(timess),2)
            predict_time = _model_time.predict(timess)
            
            text = self.Comment
            while(text.__contains__([])):
                text.remove([])      
            predict_comment = [_model.predict(tranfrom.transform(x)) for x in text]
            
            if(int(self.uic.cb_Model.currentIndex())==0):
                for idx in range(len(predict_comment)):
                    if(len(predict_comment[idx])>1):
                        if(np.array(predict_comment[idx]).tolist().count([1.]) > np.array(predict_comment[idx]).tolist().count([0.])): 
                            predict_comment[idx] = [[1.]]
                        else:
                            predict_comment[idx] = [[0.]]        
            else:
                for idx in range(len(predict_comment)):
                    if(len(predict_comment[idx])>1):
                        if(np.array(predict_comment[idx]).tolist().count(1) > np.array(predict_comment[idx]).tolist().count(0)): 
                            predict_comment[idx] = [1]
                        else:
                            predict_comment[idx] = [0]
            
            
            predict_status = [int(x) for x in np.array(predict_status).reshape(-1)]
            predict_comment = [int(x) for x in np.array(predict_comment).reshape(-1)]
            predict_time = [int(x) for x in np.array(predict_time).reshape(-1)]
            
            predict_status = predict_status.count(1) / len(predict_status) * 0.5
            predict_comment = predict_comment.count(1) / len(predict_comment) * 0.3
            predict_time = predict_time.count(1) / len(predict_time) * 0.2
            
            if(predict_status+predict_comment+predict_time>0.7):
                self.uic.label_3.setText("Có khả năng trầm cảm")
            else:
                self.uic.label_3.setText("Ít khả năng trầm cảm")
            
    def GetData(self):
        if(self.uic.txtLink.toPlainText()==""): 
            Message("Chưa nhập link FB")
        url = "https://" + self.uic.txtLink.toPlainText()
        Links = []
        Status = []
        Comment = []
        Times = []

        while(len(Status)<5 and url != None):
            driver.get(url)
            links = driver.find_elements(by=By.XPATH,value="// a[contains(text(),'Toàn bộ tin')]")
            other = driver.find_elements(by=By.XPATH,value="// span[contains(text(),'Xem tin khác')]")

            links = [Link(str(link.get_attribute("href"))) for link in links]
            other = driver.find_elements(by=By.XPATH,value="//span[contains(text(),'Xem tin khác')]")
            if(len(other)>0):
                other[0].click()
                url = driver.current_url
            else:
                url = None

            for link in links:
                driver.get(link)
                if(GetStatus()==""): continue
                else: 
                    Links.append(link)
                    Status.append(GetStatus())
                    Times.append(GetTime())
                    Comment.append(GetComment())
                    if(len(Status)==5): break
        
        self.Links = Links
        self.Status = Status
        self.Times = Times
        self.Comment = Comment
        self.df = pd.DataFrame({'Links': Links, 'Status': Status, 'Times': Times,'Comments': Comment})
        model = PandasModel(self.df.iloc[::-1])
        self.uic.tb_View.setModel(model)
        self.uic.tb_View.setWordWrap(True)
        self.uic.tb_View.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContentsOnFirstShow)
        self.uic.tb_View.horizontalHeader().setStretchLastSection(True)
    
    def show(self):
        self.main_win.show()
        
def Link(text):
    return text.split("&")[0]+"&"+text.split("&")[1]

def GetStatus():
    status=driver.find_elements(By.XPATH,"//div//p")
    if(len(status)==0): return ""
    else: return status[0].text

def GetTime():
    times=driver.find_elements(By.XPATH,"//div//abbr")
    time=times[0].text
    now = datetime.now()
    if(time.__contains__('lúc')):
        time = time[int(time.index('lúc')) + 4:]
    elif(time=='Vừa xong'): 
        time = str(now.hour)+":"+str(now.minute)
    elif(time.__contains__(' giờ')):
        now = now - timedelta(hours=int(time[:time.index('giờ')-1]))
        time = str(now.hour)+":"+str(now.minute)
    elif(time.__contains__(' phút')):
        now = now - timedelta(minutes=int(time[:time.index('phút')-1]))
        time = str(now.hour)+":"+str(now.minute)
    return time[:time.index(':')]

def GetComment():
    comment = []
    page = 0
    _url = driver.current_url
    for i in range(5):
        url = _url+"&p="+str(page)
        driver.get(url)
        parents = driver.find_elements(By.XPATH,"// div")
        for parent in parents:
            child_div = parent.find_elements(By.XPATH,"./div")
            child_h3 = parent.find_elements(By.XPATH,"./h3")
            if(len(child_div)==4 and len(child_h3)==1):
                comment.append(child_div[0].text)
        page=page+10  
    return comment

def Message(Text):
    msg=QMessageBox()
    msg.setText(Text)
    msg.exec_()
    
if __name__ == "__main__":
    app=QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show() 
    app.exec_() 