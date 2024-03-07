import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QTableWidget, QTableWidgetItem, QSizePolicy, QLabel
from bs4 import BeautifulSoup
import urllib.request
import datetime
import requests
import time
import csv
import re

# 테스트
#####################################################################################################################
# 고정된 값 : 매출, 인건비, 공과금(전기세, 수도세, 가스비), 임차료, 재료비(자재비)
# 보험, 고용보험, 산재보험

# 클래스 정의
class Store():
    name = ""
    netProfit, businessExpenses, taxPayment, totalInterestPaid, maxDeductionAmount = 0, 0, 0, 0, 0
    ownHome = True
    totalSales, totalLabor, expendables, rentInterest, donation = 0.0, 0.0, 0.0, 0.0, 0.0
    totalIncomeTax, surTax = None, None
    pensionIns, healthIns, convalscenceIns, employmentIns, occupationalIns = None, None, None, None, None
    utilities, labor, rent, ingredients = None, None, None, None
    # pTotalIncomeTax, pInsurance, pUtilities, pLabor, pRent
    # 가게명, 총매출, 자재값, 인건비, 소모품, 주담대, 기부금, 공과금
    def __init__(self,pStoreInfo):
        self.name = pStoreInfo[0]
        self.totalSales = pStoreInfo[1]
        self.ingredients = Ingredients(pStoreInfo[2])
        self.totalLabor = pStoreInfo[3]
        self.expendables = pStoreInfo[4]
        self.rentInterest = pStoreInfo[5]
        self.donation = pStoreInfo[6]
        self.utilities = Utilities(pStoreInfo[7])
        self.setInsurance()
        self.setTax()
    def setInsurance(self):
        self.pensionIns = PensionIns(self.totalLabor)
        self.healthIns = HealthIns(self.totalLabor)
        self.convalscenceIns = ConvalscenceIns(self.totalLabor)
        self.employmentIns = EmploymentIns(self.totalLabor)
        self.occupationalIns = OccupationalIns(self.totalLabor)
    def setTax(self):
        self.surTax = SurTax(self.totalSales)
        self.totalIncomeTax = TotalIncomeTax(self.totalSales)
    def testPrinting(self):
        print(f"저희 가게는 {self.name}이고 총매출:{self.totalSales},자재값:skip,인건비:{self.totalLabor},소모품:{self.expendables},주담대:{self.rentInterest},기부금:{self.donation},공과금:skip입니다\n")
    def calculateAllInsurances(self):
        print(self.pensionIns.calculation())
        print(self.healthIns.calculation())
        print(self.convalscenceIns.calculation())
        print(self.employmentIns.calculation())
        print(self.occupationalIns.calculation())
    def calculateAllTaxes(self):
        print(self.surTax.calculation())
        print(self.totalIncomeTax.calculation(self.totalSales))
    def calculateAllExpenses(self):
        print(self.utilities.calculation())
        print(self.ingredients.calculation())
    def check_consumable_expenses_deduction(self,expenses):
        """
        소모품 구매 비용에 대한 공제 가능 여부를 확인하는 함수
    
        :param expenses: 소모품 구매 비용
        :return: 공제 가능 여부에 대한 문자열
        """
        # 공제 가능 여부 확인
        if expenses > 0:
            return "소모품 구매 비용에 대한 공제가 가능합니다."
        else:
            return "소모품 구매 비용이 없거나 음수입니다. 공제가 불가능합니다."

    def check_charitable_donation_deduction(self,donation_amount, annual_income):
        """
        기부금 공제 가능 여부를 확인하는 함수
    
        :param donation_amount: 기부한 금액
        :param annual_income: 연간 근로소득
        :return: 기부금 공제 가능 여부에 대한 문자열
        """
        # 기부금 공제 가능 여부 확인
        max_deduction_amount = 0.15 * annual_income  # 연간 근로소득의 15%까지 공제 가능
        if donation_amount <= max_deduction_amount:
            return "기부금 공제 가능합니다."
        else:
            return "기부금 공제가 불가능합니다. 연간 소득 대비 기부금이 너무 많습니다."
    
    def check_mortgage_interest_deduction(self):
        """
        주택담보대출 이자 공제 여부를 확인하는 함수
    
        :param own_home: 주택 소유 여부 (True or False)
        :param total_interest_paid: 납부한 총 이자
        :param max_deduction_amount: 최대 이자 공제 가능 금액
        :return: 주택담보대출 이자 공제 여부에 대한 문자열
        """
        print("inside mortgage")
        # 주택 소유 여부 확인
        if self.ownHome:
            # 대출 이자 공제 가능 여부 확인
            if self.totalInterestPaid <= self.maxDeductionAmount:
                return "주택담보대출 이자 공제 가능합니다."
            else:
                return "대출 이자 공제가 불가능합니다. 최대 이자 공제 가능 금액을 초과했습니다."
        else:
            return "주택을 소유하고 있지 않으므로 주택담보대출 이자 공제 대상이 아닙니다."

    def tax_saving_advice(self):
        """
        세금 절약을 위한 조언을 제공하는 함수
    
        :param net_profit: 순 이익 (수익 - 비용)
        :param business_expenses: 비즈니스 운영에 소요되는 비용
        :param tax_payment: 납부할 세금
        :param own_home: 주택 소유 여부 (True or False)
        :param total_interest_paid: 납부한 총 이자
        :param max_deduction_amount: 최대 이자 공제 가능 금액
        :param expenses: 계산된 소모품 구매 비용
        :param donation_amount: 계산된 기부금
        :param annual_income: 연간 근로소득
        :return: 조언 문자열
        """
        print("advice inside")
        # 세금 절약을 위한 조언 초기화
        advice = "세금 절약을 위한 조언:\n"
    
        # 비즈니스 비용이 순 이익의 일정 비율 이하일 때
        if self.businessExpenses < self.netProfit * 0.3:
            advice += "- 비즈니스 비용을 더 효율적으로 관리하여 세금 부담을 줄이세요.\n"
            advice += "  (예: 사업용 비용을 줄이거나 비즈니스 관련 비용을 정확하게 기록하세요)\n"
        else:
            # 자격 요건에 맞게 비즈니스 비용을 공제하고 세금 혜택을 최대한 활용하는 경우
            advice += "- 비즈니스 비용을 정확하게 기록하고 가능한 모든 공제를 활용하세요.\n"
            advice += "  (예: 업무 관련 비용, 자격 요건에 맞는 공제 항목을 신청하세요)\n"
    
        # 납부할 세금이 있는 경우
        if self.taxPayment > 0:
            advice += "- 세무 전문가와 상의하여 가능한 세액 공제를 모두 활용하는 것이 좋습니다.\n"
            advice += "  (예: 세법의 변경사항을 파악하고 세액 공제 가능 여부를 확인하세요)\n"
        else:
            advice += "- 비즈니스 이익이 없거나 손실인 경우 세금 납부가 필요하지 않습니다.\n"
        print(advice)
        print("advice before mortgage")
        
        # 주택담보대출 이자 공제 여부 확인
        mortgage_deduction_result = self.check_mortgage_interest_deduction()
        advice += "- " + mortgage_deduction_result + "\n"
        print("advice before consumable")
        # 계산된 소모품 구매 비용에 대한 공제 가능 여부 확인
        consumable_expenses_deduction_result = self.check_consumable_expenses_deduction(self.expendables)
        advice += "- " + consumable_expenses_deduction_result + "\n"
        print("advice before donation")
        # 계산된 기부금에 대한 공제 가능 여부 확인
        charitable_donation_deduction_result = self.check_charitable_donation_deduction(self.donation, self.netProfit)
        advice += "- " + charitable_donation_deduction_result + "\n"
    
        return advice
    
###########################################################################
class Tax(): # 세금 - 종합소득세 , 부가세
    totalSales = 0
    def __init__(self,pTotalSales):
        self.totalSales = pTotalSales
    def calculation(self):
        print("구현이 필요합니다")
        pass

class TotalIncomeTax(Tax):
    #Profit = TotalSales - Tax - Insurance - Labor - Ingredients - Rent - Utilities
    print("insideTotalIncomeTax")
    def calculation(self,pTotalSales):
        netProfit = 0
        if pTotalSales <= 12000000.0:
            netProfit = pTotalSales * 0.06
        elif pTotalSales <= 46000000.0:
            netProfit = (pTotalSales-12000000.0) * 0.15 + 12000000.0 * 0.06
        elif pTotalSales <= 88000000.0:
            netProfit = (pTotalSales-46000000.0) * 0.24 + (46000000.0-12000000.0) * 0.15 + 12000000.0 * 0.06
        elif pTotalSales <= 150000000.0:
            netProfit = (pTotalSales-88000000.0) * 0.35 + (88000000.0-46000000.0) * 0.24 + (46000000.0-12000000.0) * 0.15 + 12000000.0 * 0.06
        elif pTotalSales <= 500000000.0:
            netProfit = (pTotalSales-150000000.0) * 0.38 + (150000000.0-88000000.0) * 0.35 + (88000000.0-46000000.0) * 0.24 + (46000000.0-12000000.0) * 0.15 + 12000000.0 * 0.06
        else:
            netProfit = (pTotalSales-500000000.0) * 0.40 + (500000000.0-150000000.0) * 0.38 + (150000000.0-88000000.0) * 0.35 + (88000000.0-46000000.0) * 0.24 + (46000000.0-12000000.0) * 0.15 + 12000000.0 * 0.06
        return netProfit

class SurTax(Tax):
    def calculation(self):
        return self.totalSales * (1/11)

##########################################################################
class Insurance(): # 보험료 - 국민연금, 건강보험, 요양보험, 고용보험, 산재보험
    totalLabor = 0.0
    def __init__(self,pTotalLabor):
        self.totalLabor = pTotalLabor
    def calculation(self):
        pass

class PensionIns(Insurance): # 국민연금
    pensionRate = 0.045
    def calculation(self):
        return self.totalLabor * self.pensionRate

class HealthIns(Insurance): # 건강보험
    healthRate = 0.03545
    def calculation(self):
        return self.totalLabor * self.healthRate

class ConvalscenceIns(Insurance): # 장기요양보험
    convalscenceRate = 0.004591
    def calculation(self):
        return self.totalLabor * self.convalscenceRate

class EmploymentIns(Insurance): # 고용보험
    employmentRate = 0.0115
    def calculation(self):
        return self.totalLabor * self.employmentRate

class OccupationalIns(Insurance): # 산재보험
    occupationalRate = 0.008
    def calculation(self):
        return self.totalLabor * self.occupationalRate

##########################################################################
class Expenses(): # 지출 - 자재값, 인건비, 소모품, 주담대, 기부금, 공과금
    totalCost = 0
    def __init__(self,pTotalCost):
        self.totalCost = pTotalCost
    def calculation():
        pass

class Utilities(Expenses):
    electricity = 0
    water = 0
    gas = 0
    def __init__(self,pElectricity=0,pWater=0,pGas=0): # 유틸리티 - 전기세, 수도세, 가스비
        self.electricity = pElectricity
        self.water = pWater
        self.gas = pGas
    def calculation(self):
        self.totalCost += (self.electricity + self.water + self.gas)
        return self.totalCost

class Ingredients(Expenses):
    def calculation(self):
        return self.totalCost

#############################################################################

#############################################################################

def on_store_select(item):
    global center_frame, right_frame
    print(storeInfoList[item.row()])
    targetIndex = item.row()
    ## 여기에서 가게정보 보여주기
    
    # 가운데 프레임에 표 추가
    center_table = QTableWidget()
    print("table initial")
    center_table.setRowCount(7)
    print("table set row count")
    center_table.setColumnCount(1)
    print("table set column count")
    #["총 매출", "인건비", "임차료", "재료비", "공과금", "소모품", "주담대", "기부금"]
    #["총 매출", "자재값", "인건비", "소모품", "주담대", "기부금", "임차료", "공과금"]
    center_table.setVerticalHeaderLabels(storeInfoHeaderList)
    print("table set headers")
    for i in range(6):
        if i == 0:
            item = QTableWidgetItem(str(myStoreList[targetIndex].totalSales))
        elif i == 1:
            item = QTableWidgetItem(str(myStoreList[targetIndex].ingredients.calculation()))
        elif i == 2:
            item = QTableWidgetItem(str(myStoreList[targetIndex].totalLabor))
        elif i == 3:
            item = QTableWidgetItem(str(myStoreList[targetIndex].expendables))
        elif i == 4:
            item = QTableWidgetItem(str(myStoreList[targetIndex].rentInterest))
        elif i == 5:
            item = QTableWidgetItem(str(myStoreList[targetIndex].donation))
        
        center_table.setItem(i, 0, item)
        
    center_layout = QVBoxLayout()
    print("layout initial")
    center_layout.addWidget(center_table)
    print("layout add")
    center_frame.setLayout(center_layout)
    print("frame set")

    # 오른쪽 프레임 레이아웃
    right_layout = QVBoxLayout()
    right_frame.setLayout(right_layout)
    
    ## 여기에서 계산정보 보여주기
    # 오른쪽 프레임 상단에 표 추가
    top_table = QTableWidget()
    top_table.setRowCount(7)
    top_table.setColumnCount(1)
    #["국민연금", "건강보험", "장기요양보험", "고용보험", "산재보험", "부가가치세", "종합소득세"]
    top_table.setVerticalHeaderLabels(storeCalculationHeaderList)
    for i in range(7):
        print("포문 들어옴")
        if i == 0:
            item_top = QTableWidgetItem(str(myStoreList[targetIndex].pensionIns.calculation()))
        elif i == 1:
            item_top = QTableWidgetItem(str(myStoreList[targetIndex].healthIns.calculation()))
        elif i == 2:
            item_top = QTableWidgetItem(str(myStoreList[targetIndex].convalscenceIns.calculation()))
        elif i == 3:
            item_top = QTableWidgetItem(str(myStoreList[targetIndex].employmentIns.calculation()))
        elif i == 4:
            item_top = QTableWidgetItem(str(myStoreList[targetIndex].occupationalIns.calculation()))
        elif i == 5:
            item_top = QTableWidgetItem(str(myStoreList[targetIndex].pensionIns.calculation()))
        elif i == 6:
            item_top = QTableWidgetItem(str(myStoreList[targetIndex].pensionIns.calculation()))
        top_table.setItem(i, 0, item_top)
    right_layout.addWidget(top_table)

    ## 여기에서 어드바이스정보 보여주기
    # 오른쪽 프레임 하단에 표 추가
    bottom_table = QTableWidget()
    bottom_table.setRowCount(1)
    bottom_table.setColumnCount(1)
    bottom_table.setVerticalHeaderLabels(["Advice"])
    print("advice before")
    item_bottom = QTableWidgetItem(str(myStoreList[targetIndex].tax_saving_advice()))
    print("advice after")
    print(myStoreList[targetIndex].tax_saving_advice())
    bottom_table.setItem(0, 0, item_bottom)

    bottom_table.resizeColumnsToContents()
    bottom_table.resizeRowsToContents()

    right_layout.addWidget(bottom_table)
    #for row in range(4):
    #    for column in range(2):
    #        item_bottom = QTableWidgetItem(f"Bottom Row {row+1}, Column {column+1}")
    #        bottom_table.setItem(row, column, item_bottom)
    #right_layout.addWidget(bottom_table)

## 전역변수
crawlingList = [
    ["kimbop-heaven","#comp-j82zpp8j > h1","#comp-j82zpp8b"],
    ["paris-baguette","#comp-j82zugry > h1","#comp-j82zugn91"],
    ["jjampong-town","#comp-j82zyvtb > h1 > span > span","#comp-j82zyvsl"],
    ["ugane","#comp-j83048cm > h1","#comp-j83048bi1"],
    ["bbq","#comp-j83083i0 > h1","#comp-j83083h8"],
    ["lotteria","#comp-j830bu6t > h1","#comp-j830bu6m"]
    ]
csvName = "C:/Projects/Project1_WorkAutomation/result/store_info.csv"
storeInfoHeaderList = ["총 매출", "자재값", "인건비", "소모품", "주담대", "기부금", "임차료", "공과금"]
storeCalculationHeaderList = ["국민연금", "건강보험", "장기요양보험", "고용보험", "산재보험", "부가가치세", "종합소득세"]
center_frame, right_frame = None, None

if __name__ == "__main__":
    for storeUrl in crawlingList:
        url = f"https://mingihong.wixsite.com/fiveman/{storeUrl[0]}"
        # print(url)
        htmlObeject = urllib.request.urlopen(url)
        ## 유알엘을 리퀘스트
        webPage = htmlObeject.read()
        bsObject = BeautifulSoup(webPage, 'html.parser')
            ## html 파일을 받음 
            ## beautifulsoup 사용 
        store_name = storeUrl[1].split(' > ')[0].replace('#', '')
        name_info = bsObject.find('div', {'id': store_name}).text.strip()
            ## 제목받아오기 storeUrl 안에 있음 soup.select_one("변수")
        tax = storeUrl[2].split(' > ')[0].replace('#', '')
        tax_info = bsObject.find('div', {'id': tax}).text.strip()
        # 세금 항목 숫자만 표시되게 하기
        tax_info = re.sub(r'\D', ',', tax_info)
        # 항목 구분 쉼표 한번만 나오게 하기
        tax_info = re.sub(r',+', ',', tax_info)
        print(name_info, tax_info)
            # 가게 이름과 세금 정보 CSV 파일에 쓰기
        store_infolist = [name_info, tax_info]
        with open(csvName, 'a', newline = '', encoding = 'utf-8') as csvFp :
            csvFp.write(' '.join(store_infolist) + '\n')

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Layout Example")
    window.resize(1200, 900)

    # 메인 레이아웃
    main_layout = QHBoxLayout()
    window.setLayout(main_layout)

    # 왼쪽 프레임
    left_frame = QFrame()
    left_frame.setFrameShape(QFrame.StyledPanel)
    left_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 왼쪽 프레임에 표 추가
    storeNameList = []
    myStore = None
    global storeInfoList
    storeInfoList = []
    left_table = QTableWidget()
    global myStoreList
    myStoreList = []
    left_table.clicked.connect(on_store_select)
    left_table.setRowCount(6)
    left_table.setColumnCount(1)
    
    with open(csvName, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            tempList = [row[0],int(row[1]),int(row[2]),int(row[3]),int(row[4]),int(row[5]),int(row[6]),1000]
            myStore = Store(tempList)
            myStore.setInsurance()
            myStore.setTax()
            myStoreList.append(myStore)
            storeNameList.append(row[0])
            rowList = []
            rowList.append(row[1])
            rowList.append(row[2])
            rowList.append(row[3])
            rowList.append(row[4])
            rowList.append(row[5])
            rowList.append(row[6])
            storeInfoList.append(rowList)
    file.close()
    left_table.setVerticalHeaderLabels(storeNameList)
    for row in range(6):
        for column in range(6):
            item = QTableWidgetItem("정보 보기")
            left_table.setItem(row, column, item)
    left_layout = QVBoxLayout()
    left_layout.addWidget(left_table)
    left_frame.setLayout(left_layout)

    # 가운데 프레임
    center_frame = QFrame()
    center_frame.setFrameShape(QFrame.StyledPanel)
    center_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 오른쪽 프레임
    right_frame = QFrame()
    right_frame.setFrameShape(QFrame.StyledPanel)
    right_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 메인 레이아웃에 프레임 추가
    main_layout.addWidget(left_frame)
    main_layout.addWidget(center_frame)
    main_layout.addWidget(right_frame)

    window.show()
    sys.exit(app.exec_())
