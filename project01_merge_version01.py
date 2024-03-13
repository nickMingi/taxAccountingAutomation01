import sys
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QTableWidget, QTableWidgetItem, QSizePolicy, QLabel, QPushButton, QMenuBar, QAction, QStackedWidget, QMainWindow, QMenu
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bs4 import BeautifulSoup
import urllib.request
import datetime
import requests
import time
import csv
import re
import os
from PyQt5.QtGui import QColor

# 테스트
#####################################################################################################################
# 고정된 값 : 매출, 인건비, 공과금(전기세, 수도세, 가스비), 임차료, 재료비(자재비)
# 보험, 고용보험, 산재보험

# 클래스 정의
class Store():
    name = ""
    netProfit, businessExpenses, taxPayment, totalInterestPaid, maxDeductionAmount = 0, 0, 0, 0, 0
    ownHome = True
    totalSales, ingredients, totalLabor, expendables, rentInterest, rentFee, utilities, donation = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    totalIncomeTax, surTax = None, None
    pensionIns, healthIns, convalescenceIns, employmentIns, occupationalIns = None, None, None, None, None
    # 가게명, 총매출, 자재값, 인건비, 소모품, 주담대, 기부금, 공과금
    def __init__(self,pStoreInfo):
        self.name = pStoreInfo[0]
        self.totalSales = pStoreInfo[1]
        self.ingredients = pStoreInfo[2]
        self.totalLabor = pStoreInfo[3]
        self.expendables = pStoreInfo[4]
        self.rentInterest = pStoreInfo[5]
        self.rentFee = pStoreInfo[6]
        self.utilities = pStoreInfo[7]
        self.donation = pStoreInfo[8]
        self.totalCost = self.ingredients + self.totalLabor + self.expendables + self.rentInterest + self.rentFee + self.utilities + self.donation
        self.netProfit = self.totalSales - self.totalCost
        self.setInsurance()
        self.setTax()
        if self.rentInterest == 0.0:
            self.ownHome = False
    def setInsurance(self):
        self.pensionIns = PensionIns(self.totalLabor)
        self.healthIns = HealthIns(self.totalLabor)
        self.convalescenceIns = ConvalescenceIns(self.totalLabor)
        self.employmentIns = EmploymentIns(self.totalLabor)
        self.occupationalIns = OccupationalIns(self.totalLabor)
    def setTax(self):
        self.surTax = SurTax(self.totalSales, self.netProfit)
        self.totalIncomeTax = TotalIncomeTax(self.totalSales, self.netProfit)
        self.taxPayment = self.totalIncomeTax.calculation()
    def check_consumable_expenses_deduction(self):
        advice2 = ""
        """
        소모품 구매 비용에 대한 공제 가능 여부를 확인하는 함수
    
        :param expenses: 소모품 구매 비용
        :return: 공제 가능 여부에 대한 문자열
        """
        # 공제 가능 여부 확인
        if self.expendables > 0:
            annual_bottom_label2.setStyleSheet("font-weight: bold; color: blue; font-size: 15px; ")
            advice2 += "- 소모품 구매 비용에 대한 공제가 가능합니다."
        else:
            annual_bottom_label2.setStyleSheet("font-weight: bold; color: red; font-size: 15px; ")
            advice2 += "- 소모품 구매 비용이 없거나 음수입니다. \n  공제가 불가능합니다."
        return advice2

    def check_charitable_donation_deduction(self):
        advice3 = ""
        """
        기부금 공제 가능 여부를 확인하는 함수
    
        :param donation_amount: 기부한 금액
        :param annual_income: 연간 근로소득
        :return: 기부금 공제 가능 여부에 대한 문자열
        """
        # 기부금 공제 가능 여부 확인
        max_deduction_amount = 0.15 * self.netProfit  # 연간 근로소득의 15%까지 공제 가능
        if self.donation <= max_deduction_amount:
            annual_bottom_label3.setStyleSheet("font-weight: bold; color: blue; font-size: 15px; ")
            advice3 += "- 기부금 공제 가능합니다."
        else:
            annual_bottom_label3.setStyleSheet("font-weight: bold; color: red; font-size: 15px; ")
            advice3 += "- 기부금 공제가 불가능합니다. \n  연간 소득 대비 기부금이 너무 많습니다."
        return advice3
    
    def check_mortgage_interest_deduction(self):
        advice4 = ""
        """
        주택담보대출 이자 공제 여부를 확인하는 함수
    
        :param own_home: 주택 소유 여부 (True or False)
        :param total_interest_paid: 납부한 총 이자
        :param max_deduction_amount: 최대 이자 공제 가능 금액
        :return: 주택담보대출 이자 공제 여부에 대한 문자열
        """
        print("inside mortgage")
        # 주택 소유 여부 확인
        max_deduction_amount = 0.15 * self.netProfit
        if self.ownHome:
            # 대출 이자 공제 가능 여부 확인
            if self.rentInterest <= max_deduction_amount:
                annual_bottom_label4.setStyleSheet("font-weight: bold; color: blue; font-size: 15px; ")
                advice4 += "- 주택담보대출 이자 공제 가능합니다."
            else:
                annual_bottom_label4.setStyleSheet("font-weight: bold; color: red; font-size: 15px; ")
                advice4 += "- 대출 이자 공제가 불가능합니다.\n  최대 이자 공제 가능 금액을 초과했습니다."
        else:
            annual_bottom_label4.setStyleSheet("font-weight: bold; color: red; font-size: 15px; ")
            return "- 주택을 소유하고 있지 않으므로\n  주택담보대출 이자 공제 대상이 아닙니다."
        return advice4

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
        if self.totalCost < self.netProfit * 0.3:
            annual_bottom_label1.setStyleSheet("font-weight: bold; color: blue; font-size: 15px; ")
            advice += "- 비즈니스 비용을 더 효율적으로\n  관리하여 세금 부담을 줄이세요.\n"
            advice += "  (예: 사업용 비용을 줄이거나 비즈니스\n  관련 비용을 정확하게 기록하세요)\n"
        else:
            annual_bottom_label1.setStyleSheet("font-weight: bold; color: red; font-size: 15px; ")
            # 자격 요건에 맞게 비즈니스 비용을 공제하고 세금 혜택을 최대한 활용하는 경우
            advice += "- 비즈니스 비용을 정확하게 기록하고\n  가능한 모든 공제를 활용하세요.\n"
            advice += "  (예: 업무 관련 비용, 자격 요건에\n  맞는 공제 항목을 신청하세요)\n"
    
        # 납부할 세금이 있는 경우
        if self.taxPayment > 0.0:
            annual_bottom_label1.setStyleSheet("font-weight: bold; color: blue; font-size: 15px; ")
            advice += "- 세무 전문가와 상의하여 가능한\n  세액 공제를 모두 활용하는 것이 좋습니다.\n"
            advice += "  (예: 세법의 변경사항을 파악하고\n  세액 공제 가능 여부를 확인하세요)"
        else:
            annual_bottom_label1.setStyleSheet("font-weight: bold; color: red; font-size: 15px; ")
            advice += "- 비즈니스 이익이 없거나 손실인 경우\n  세금 납부가 필요하지 않습니다."
    
        return advice

############################################################################

class Employee():
    name = ""
    age, phone, totalLabor = 0, 0, 0.0
    pensionIns, healthIns, convalescenceIns, employmentIns, occupationalIns = None, None, None, None, None
    def __init__(self, pEmployeeInfo):
        self.name = pEmployeeInfo[0]
        self.age = pEmployeeInfo[1]
        self.phone = pEmployeeInfo[2]
        self.totalLabor = pEmployeeInfo[3]
        self.setInsurance()
    def setInsurance(self):
        self.pensionIns = PensionIns(self.totalLabor)
        self.healthIns = HealthIns(self.totalLabor)
        self.convalescenceIns = ConvalescenceIns(self.totalLabor)
        self.employmentIns = EmploymentIns(self.totalLabor)

###########################################################################
class Tax(): # 세금 - 종합소득세 , 부가세
    totalSales, netProfit = 0.0, 0.0
    def __init__(self,pTotalSales,pNetProfit):
        self.totalSales = pTotalSales
        self.netProfit = pNetProfit
    def calculation(self):
        pass

class TotalIncomeTax(Tax):
    def calculation(self):
        if self.netProfit <= 12000000.0:
            return self.netProfit * 0.06
        elif self.netProfit <= 46000000.0:
            return (self.netProfit-12000000.0) * 0.15 + 12000000.0 * 0.06
        elif self.netProfit <= 88000000.0:
            return (self.netProfit-46000000.0) * 0.24 + (46000000.0-12000000.0) * 0.15 + 12000000.0 * 0.06
        elif self.netProfit <= 150000000.0:
            return (self.netProfit-88000000.0) * 0.35 + (88000000.0-46000000.0) * 0.24 + (46000000.0-12000000.0) * 0.15 + 12000000.0 * 0.06
        elif self.netProfit <= 500000000.0:
            return (self.netProfit-150000000.0) * 0.38 + (150000000.0-88000000.0) * 0.35 + (88000000.0-46000000.0) * 0.24 + (46000000.0-12000000.0) * 0.15 + 12000000.0 * 0.06
        else:
            return (self.netProfit-500000000.0) * 0.40 + (500000000.0-150000000.0) * 0.38 + (150000000.0-88000000.0) * 0.35 + (88000000.0-46000000.0) * 0.24 + (46000000.0-12000000.0) * 0.15 + 12000000.0 * 0.06

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

class ConvalescenceIns(Insurance): # 장기요양보험
    convalescenceRate = 0.004591
    def calculation(self):
        return self.totalLabor * self.convalescenceRate

class EmploymentIns(Insurance): # 고용보험
    employmentRate = 0.0115
    def calculation(self):
        return self.totalLabor * self.employmentRate

class OccupationalIns(Insurance): # 산재보험
    occupationalRate = 0.008
    def calculation(self):
        return self.totalLabor * self.occupationalRate

##########################################################################
class Expenses(): # 지출 - 재료비, 인건비, 소모품, 주담대, 임차료, 공과금, 기부금
    totalCost = 0
    def __init__(self,pTotalCost):
        self.totalCost = pTotalCost
    def calculation():
        pass

class Ingredients(Expenses):
    def __init__(self, pIngredients):
        self.ingredients = pIngredients
    def calculation(self):
        self.totalCost += self.ingredients
        return self.totalCost
    
class Labor(Expenses):
    def __init__(self, pTotalLabor):
        self.totalLabor = pTotalLabor
    def calculation(self):
        self.totalCost += self.totalLabor
        return self.totalCost

class Expendables(Expenses):
    def __init__(self, pExpendables):
        self.expendables = pExpendables
    def calculation(self):
        self.totalCost += self.expendables
        return self.totalCost

class RentInterest(Expenses):
    def __init__(self, pRentInterest):
        self.rentInterest = pRentInterest
    def calculation(self):
        self.totalCost += self.rentInterest
        return self.totalCost

class RentFee(Expenses):
    def __init__(self, pRentFee):
        self.rentFee = pRentFee
    def calculation(self):
        self.totalCost += self.rentFee
        return self.totalCost

class Donation(Expenses):
    def __init__(self, pDonation):
        self.donation = pDonation
    def calculation(self):
        self.totalCost += self.donation
        return self.totalCost
    
class Utilities(Expenses):
    def __init__(self, pUtilities):
        self.utilities = pUtilities
    def calculation(self):
        self.totalCost += self.utilities
        return self.totalCost
    

#############################################################################
def save_to_pdf():
    # PDF 생성
    c = canvas.Canvas("store_info.pdf", pagesize=letter)

    pdfmetrics.registerFont(TTFont("맑은고딕", "malgun.ttf"))
    c.setFont("맑은고딕", 16)

    # 선택된 가게 정보 가져오기
    selected_store_index = annual_left_table.currentRow()
    selected_store = myStoreList[selected_store_index]

    # PDF에 가게 정보 추가
    c.drawString(100, 750, "가게 정보")
    c.drawString(100, 730, f"가게명: {selected_store.name}")
    c.drawString(100, 710, f"총 매출: {selected_store.totalSales}")
    c.drawString(100, 690, f"재료비: {selected_store.ingredients}")
    c.drawString(100, 670, f"인건비: {selected_store.totalLabor}")
    c.drawString(100, 650, f"소모품: {selected_store.expendables}")
    c.drawString(100, 630, f"주담대: {selected_store.rentInterest}")
    c.drawString(100, 610, f"임차료: {selected_store.rentFee}")
    c.drawString(100, 590, f"공과금: {selected_store.utilities}")
    c.drawString(100, 570, f"기부금: {selected_store.donation}")

    # PDF에 계산된 세금 정보 추가
    c.drawString(100, 530, "계산된 세금 정보")
    c.drawString(100, 510, f"국민연금: {selected_store.pensionIns.calculation()}")
    c.drawString(100, 490, f"건강보험: {selected_store.healthIns.calculation()}")
    c.drawString(100, 470, f"장기요양보험: {selected_store.convalescenceIns.calculation()}")
    c.drawString(100, 450, f"고용보험: {selected_store.employmentIns.calculation()}")
    c.drawString(100, 430, f"산재보험: {selected_store.occupationalIns.calculation()}")
    c.drawString(100, 410, f"부가가치세: {selected_store.surTax.calculation()}")
    c.drawString(100, 390, f"종합소득세: {selected_store.totalIncomeTax.calculation()}")

    # PDF에 어드바이스 정보 추가
    c.drawString(100, 350, "")
    advice = selected_store.tax_saving_advice()
    advice_lines = advice.split("\n")
    y_position = 350
    for line in advice_lines:
        c.drawString(100, y_position, line)
        y_position -= 20

    # PDF 저장
    c.save()
#############################################################################
def on_store_select(item):
    global annual_center_frame, annual_right_frame, annual_innerFrameList, annual_topInnerFrameList
    targetIndex = item.row()
    ## 여기에서 가게정보 보여주기

    if annual_innerFrameList[targetIndex] != None:
        for i in range(len(annual_innerFrameList)):
            if i != targetIndex:
                annual_innerFrameList[i].hide()
            else:
                annual_innerFrameList[i].show()
    else:
        print("테이블 만들기 에러")
        return
    
    if annual_topInnerFrameList[targetIndex] != None:
        for i in range(len(annual_topInnerFrameList)):
            if i != targetIndex:
                annual_topInnerFrameList[i].hide()
            else:
                annual_topInnerFrameList[i].show()
    else:
        print("테이블 만들기 에러")
        return

    # 가운데 프레임에 표 추가
    annual_center_table = QTableWidget()
    annual_center_table.setRowCount(8)
    annual_center_table.setColumnCount(3)
    #["총 매출", "재료비", "인건비", "소모품", "주담대", "임차료", "공과금", "기부금"]
    annual_center_table.setVerticalHeaderLabels(storeInfoHeaderList)
    
    with open(r'./store_info_2022.csv', 'r', encoding='utf-8') as file:
        inFile = csv.reader(file)
        comList = list(inFile)

        for i in range(8):
            if i == 0:
                item = QTableWidgetItem(str(myStoreList[targetIndex].totalSales))
            elif i == 1:
                item = QTableWidgetItem(str(myStoreList[targetIndex].ingredients))
            elif i == 2:
                item = QTableWidgetItem(str(myStoreList[targetIndex].totalLabor))
            elif i == 3:
                item = QTableWidgetItem(str(myStoreList[targetIndex].expendables))
            elif i == 4:
                item = QTableWidgetItem(str(myStoreList[targetIndex].rentInterest))
            elif i == 5:
                item = QTableWidgetItem(str(myStoreList[targetIndex].rentFee))
            elif i == 6:
                item = QTableWidgetItem(str(myStoreList[targetIndex].utilities))
            elif i == 7:
                item = QTableWidgetItem(str(myStoreList[targetIndex].donation))
            
            annual_center_table.setItem(i, 0, item)

            for j in range(1,9) :
                selected_row = annual_left_table.currentRow()  # 왼쪽 테이블의 행 번호를 가져오기
                value = comList[selected_row][j]
                annual_center_table.setItem(j-1,1,QTableWidgetItem(str(value)))

        for m in range(8): 
            firstItem = annual_center_table.item(m, 0).text()
            firstValue = int(firstItem)
            secondItem = annual_center_table.item(m, 1).text()
            secondValue = int(secondItem)

            try :
                percentValue = (firstValue-secondValue)/firstValue*100
                rounded_percentValue = round(percentValue, 2)
                rpv = rounded_percentValue
                if rpv > 0 :
                    rpv = "+" + str(rpv) + "%"
                elif rpv < 0 :
                    rpv = str(rpv) + '%'
            except :
                rpv = 0

            item = QTableWidgetItem(str(rpv))
            if rounded_percentValue > 0:
                item.setForeground(QColor('red'))  # 글자색을 빨간색으로 설정
            elif rounded_percentValue < 0:
                item.setForeground(QColor('blue'))  # 글자색을 파란색으로 설정

            annual_center_table.setItem(m, 2, item)

    annual_center_layout = QVBoxLayout()
    annual_center_layout.addWidget(annual_center_table)
    annual_innerFrameList[targetIndex].setLayout(annual_center_layout)

    # 오른쪽 프레임 레이아웃
    annual_right_layout = QVBoxLayout()
    annual_right_frame.setLayout(annual_right_layout)
    
    # 여기에서 계산된 정보 보여주기
    # 오른쪽 프레임 상단에 표 추가
    annual_top_table = QTableWidget()
    annual_top_table.setRowCount(7)
    annual_top_table.setColumnCount(1)
    #["국민연금", "건강보험", "장기요양보험", "고용보험", "산재보험", "부가가치세", "종합소득세"]
    annual_top_table.setVerticalHeaderLabels(storeCalculationHeaderList)
    for i in range(7):
        if i == 0:
            item_top = QTableWidgetItem(str(int(myStoreList[targetIndex].pensionIns.calculation())))
        elif i == 1:
            item_top = QTableWidgetItem(str(int(myStoreList[targetIndex].healthIns.calculation())))
        elif i == 2:
            item_top = QTableWidgetItem(str(int(myStoreList[targetIndex].convalescenceIns.calculation())))
        elif i == 3:
            item_top = QTableWidgetItem(str(int(myStoreList[targetIndex].employmentIns.calculation())))
        elif i == 4:
            item_top = QTableWidgetItem(str(int(myStoreList[targetIndex].occupationalIns.calculation())))
        elif i == 5:
            item_top = QTableWidgetItem(str(int(myStoreList[targetIndex].surTax.calculation())))
        elif i == 6:
            item_top = QTableWidgetItem(str(int(myStoreList[targetIndex].totalIncomeTax.calculation())))
        annual_top_table.setItem(i, 0, item_top)
    annual_top_table.setEnabled(False)
    annual_right_layout.addWidget(annual_top_table)
    annual_topInnerFrameList[targetIndex].setLayout(annual_right_layout)


    ## 여기에서 어드바이스정보 보여주기
    # 오른쪽 프레임 하단에 라벨 추가
    global annual_bottom_label1, annual_bottom_label2, annual_bottom_label3, annual_bottom_label4, annual_button_btn
    annual_bottom_label1 = QLabel()
    annual_bottom_label1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    annual_bottom_label1.setText(str(myStoreList[targetIndex].tax_saving_advice()))
    annual_bottom_label1.setEnabled(False)
    annual_right_layout.addWidget(annual_bottom_label1)

    annual_bottom_label2 = QLabel()
    annual_bottom_label2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    annual_bottom_label2.setText(str(myStoreList[targetIndex].check_consumable_expenses_deduction()))
    annual_bottom_label2.setEnabled(False)
    annual_right_layout.addWidget(annual_bottom_label2)

    annual_bottom_label3 = QLabel()
    annual_bottom_label3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    annual_bottom_label3.setText(str(myStoreList[targetIndex].check_charitable_donation_deduction()))
    annual_bottom_label3.setEnabled(False)
    annual_right_layout.addWidget(annual_bottom_label3)

    annual_bottom_label4 = QLabel()
    annual_bottom_label4.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    annual_bottom_label4.setText(str(myStoreList[targetIndex].check_mortgage_interest_deduction()))
    annual_bottom_label4.setEnabled(False)
    annual_right_layout.addWidget(annual_bottom_label4)

    annual_button_btn = QPushButton("PDF로 저장")
    annual_button_btn.setEnabled(True)
    annual_button_btn.clicked.connect(save_to_pdf)
    annual_right_layout.addWidget(annual_button_btn)

def private_store_select(item2):
    global private_center_frame, private_center_innerFrameList
    global targetIndex2
    targetIndex2 = item2.row()
    # 가게 직원 정보

    private_center_parent_layout = QHBoxLayout()
    for i in range(len(storeNameList)):
        private_center_innerFrame = QFrame()
        private_center_innerFrame.setFrameShape(QFrame.StyledPanel)
        private_center_innerFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        private_center_innerFrameList.append(private_center_innerFrame)
        private_center_parent_layout.addWidget(private_center_innerFrame)
    private_center_frame.setLayout(private_center_parent_layout)

    if private_center_innerFrameList[targetIndex2] != None:
        for i in range(len(private_center_innerFrameList)):
            if i != targetIndex2:
                private_center_innerFrameList[i].hide()
            else:
                private_center_innerFrameList[i].show()
    else:
        print("테이블 만들기 에러")
        return

    # 가운데 프레임에 표 추가
    private_center_table = QTableWidget()
    private_center_table.setRowCount(len(employee_dict[targetIndex2]['이름']))
    private_center_table.setColumnCount(1)
    private_center_table.setVerticalHeaderLabels(employee_dict[targetIndex2]['이름'])

    for row in range(len(employee_dict[targetIndex2]['이름'])):
        for column in range(len(employee_dict[targetIndex2]['이름'])):
            item = QTableWidgetItem("정보 보기")
            private_center_table.setItem(row, column, item)

    private_center_layout = QVBoxLayout()
    private_center_layout.addWidget(private_center_table)
    private_center_innerFrameList[targetIndex2].setLayout(private_center_layout)

    private_center_table.clicked.connect(on_employee_select)

def on_employee_select(item3):
    global private_right_frame
    
    targetIndex3 = item3.row()
            
    for i in range(3):
        item4 = QTableWidgetItem(employee_dict[targetIndex2][privateHeaderList[i]][targetIndex3])
        private_right_table.setItem(i, 0, item4)

    Insrate = [0.045, 0.03545, 0.004591, 0.009]
    for j in range(3, 7):
        salaryValue = float(employee_dict[targetIndex2]['연봉'][targetIndex3])
        item5 = QTableWidgetItem(str(salaryValue * Insrate[j-3]))
        private_right_table.setItem(j, 0, item5)
    private_right_table.setEnabled(False)
    
    
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
employee_csvNameList = ["./management/kimbab.csv", "./management/paris.csv", 
                        "./management/jjambbong.csv", "./management/yougane.csv",
                        "./bbq.csv", "./management/lotteria.csv"]

# 파일 경로에서 폴더 경로 추출
folder_path = os.path.dirname(csvName)

# 폴더가 존재하지 않으면 생성
if not os.path.exists(folder_path) :
    os.makedirs(folder_path)

storeInfoHeaderList = ["총 매출", "재료비", "인건비", "소모품", "주담대", "임차료", "공과금", "기부금"]
storeCalculationHeaderList = ["국민연금", "건강보험", "장기요양보험", "고용보험", "산재보험", "부가가치세", "종합소득세"]
annual_center_frame, annual_right_frame = None, None
annual_innerFrameList = []
annual_topInnerFrameList = []

privateHeaderList = ["이름", "나이", "연봉", "국민연금", "건강보험", "장기요양보험", "고용보험"]
private_center_frame, private_right_frame = None, None
private_center_innerFrameList = []
private_right_innerFrameList = []

if __name__ == "__main__":
    fileCreated = False
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
        if fileCreated == False:
            with open(csvName, 'w', newline = '', encoding = 'utf-8') as csvFp :
                csvFp.write(' '.join(store_infolist) + '\n')
            fileCreated = True
        else:
            with open(csvName, 'a', newline = '', encoding = 'utf-8') as csvFp :
                csvFp.write(' '.join(store_infolist) + '\n')

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    main_window.setWindowTitle("세무/회계 자동화 프로그램")
    main_window.resize(1200, 900)
    stacked_widget = QStackedWidget()
    widget1 = QWidget()
    widget2 = QWidget()
    
    # 왼쪽 프레임
    annual_left_frame = QFrame()
    annual_left_frame.setFrameShape(QFrame.StyledPanel)
    annual_left_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    private_left_frame = QFrame()
    private_left_frame.setFrameShape(QFrame.StyledPanel)
    private_left_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 왼쪽 프레임에 표 추가
    storeNameList = []
    myStore = None
    annual_left_table = QTableWidget()
    global myStoreList
    myStoreList = []
    annual_left_table.clicked.connect(on_store_select)
    annual_left_table.setRowCount(len(crawlingList))
    annual_left_table.setColumnCount(1)

    private_left_table = QTableWidget()
    private_left_table.clicked.connect(private_store_select)
    private_left_table.setRowCount(len(crawlingList))
    private_left_table.setColumnCount(1)
    
    with open(csvName, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            tempList = [row[0],int(row[1]),int(row[2]),int(row[3]),int(row[4]),int(row[5]),int(row[6]),int(row[7]),int(row[8])]
            myStore = Store(tempList)
            myStore.setInsurance()
            myStore.setTax()
            myStoreList.append(myStore)
            storeNameList.append(row[0])
    file.close()
    annual_left_table.setVerticalHeaderLabels(storeNameList)
    for row in range(len(crawlingList)):
        for column in range(len(crawlingList)):
            item = QTableWidgetItem("정보 보기")
            annual_left_table.setItem(row, column, item)

    employee_dict = {}

    for i, employee_csvName in enumerate(employee_csvNameList):
        with open(employee_csvName, 'r', encoding='utf-8') as eFile:
            reader = csv.reader(eFile)
            rows = list(reader)
            keys = rows[0]
            values = rows[1:]
            employee_dict[i] = {key: value for key, value in zip(keys, zip(*values))}
    
    annual_left_layout = QVBoxLayout()
    annual_left_layout.addWidget(annual_left_table)

    private_left_table.setVerticalHeaderLabels(storeNameList)
    for row in range(len(crawlingList)):
        for column in range(len(crawlingList)):
            item = QTableWidgetItem("정보 보기")
            private_left_table.setItem(row, column, item)
    
    private_left_layout = QVBoxLayout()
    private_left_layout.addWidget(private_left_table)

    # 광고 이미지 추가
    pixmap_list = []
    image_paths = ['./advertisement/adv1.jpg', './advertisement/adv2.jpg', './advertisement/adv3.jpg']
    
    for path in image_paths:
        pixmap = QPixmap(path)
        pixmap_list.append(pixmap)

    # 왼쪽 프레임에 라벨 추가
    annual_left_bottom_label = QLabel()
    annual_timer = QTimer(annual_left_bottom_label)
    annual_left_bottom_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    annual_left_bottom_label.setPixmap(pixmap_list[0])
    annual_timer.setInterval(5000)
    annual_timer.setSingleShot(False)  # 단일 실행 모드 해제

    private_left_bottom_label = QLabel()
    private_timer = QTimer(private_left_bottom_label)
    private_left_bottom_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    private_left_bottom_label.setPixmap(pixmap_list[0])
    private_timer.setInterval(5000)
    private_timer.setSingleShot(False)  # 단일 실행 모드 해제

    current_index = 0
    def change_image():
        global current_index
        next_index = (current_index + 1) % len(pixmap_list)
        annual_left_bottom_label.setPixmap(pixmap_list[next_index])
        current_index = next_index

    private_current_index = 0
    def private_change_image():
        global private_current_index
        private_next_index = (private_current_index + 1) % len(pixmap_list)
        private_left_bottom_label.setPixmap(pixmap_list[private_next_index])
        private_current_index = private_next_index

    annual_timer.timeout.connect(change_image)
    annual_timer.start()

    private_timer.timeout.connect(private_change_image)
    private_timer.start()

    annual_left_layout.addWidget(annual_left_bottom_label)
    annual_left_frame.setLayout(annual_left_layout)

    private_left_layout.addWidget(private_left_bottom_label)
    private_left_frame.setLayout(private_left_layout)

    # 가운데 프레임
    annual_center_frame = QFrame()
    annual_center_frame.setFrameShape(QFrame.StyledPanel)
    annual_center_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    private_center_frame = QFrame()
    private_center_frame.setFrameShape(QFrame.StyledPanel)
    private_center_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    annual_center_parent_layout = QHBoxLayout()
    for item in range(len(crawlingList)):
        annual_innerFrame = QFrame()
        annual_innerFrame.setFrameShape(QFrame.StyledPanel)
        annual_innerFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        annual_innerFrameList.append(annual_innerFrame)
        annual_center_parent_layout.addWidget(annual_innerFrame)
        annual_innerFrame.setEnabled(False)
    annual_center_frame.setLayout(annual_center_parent_layout)

    # 오른쪽 프레임
    annual_right_frame = QFrame()
    annual_right_frame.setFrameShape(QFrame.StyledPanel)
    annual_right_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    private_right_frame = QFrame()
    private_right_frame.setFrameShape(QFrame.StyledPanel)
    private_right_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # 오른쪽 프레임 레이아웃
    private_right_layout = QVBoxLayout()
    private_right_frame.setLayout(private_right_layout)

    # 여기에서 계산된 정보 보여주기
    # 오른쪽 프레임 상단에 표 추가
    private_right_table = QTableWidget()
    private_right_table.setRowCount(7)
    private_right_table.setColumnCount(1)
    #["이름", "나이", "전화번호", "연봉", "국민연금", "건강보험", "장기요양보험", "고용보험"]
    private_right_table.setVerticalHeaderLabels(privateHeaderList)
    private_right_layout.addWidget(private_right_table)

    annual_right_parent_layout = QHBoxLayout()
    for item in range(len(crawlingList)):
        annual_topInnerFrame = QFrame()
        annual_topInnerFrame.setFrameShape(QFrame.StyledPanel)
        annual_topInnerFrame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        annual_topInnerFrameList.append(annual_topInnerFrame)
        annual_right_parent_layout.addWidget(annual_topInnerFrame)
    annual_right_frame.setLayout(annual_right_parent_layout)

    # 메뉴바 구성
    menubar = QMenuBar(main_window)
    menubar.resize(185, 22)

    annual_tax_menu = QMenu('Annual Tax')
    annual_tax_action = QAction('Annual Tax', main_window)
    
    private_insurance_menu =QMenu('Private Insurance')
    private_insurance_action = QAction('Private Insurance', main_window)

    # 연간 레이아웃
    annual_tax_layout = QHBoxLayout()
    annual_tax_layout.addWidget(annual_left_frame)
    annual_tax_layout.addWidget(annual_center_frame)
    annual_tax_layout.addWidget(annual_right_frame)

    # 직원 관리 레이아웃
    private_insurance_layout = QHBoxLayout()
    private_insurance_layout.addWidget(private_left_frame)
    private_insurance_layout.addWidget(private_center_frame)
    private_insurance_layout.addWidget(private_right_frame)

    widget1.setLayout(annual_tax_layout)
    widget2.setLayout(private_insurance_layout)
    stacked_widget.addWidget(widget1)
    stacked_widget.addWidget(widget2)

    annual_tax_action.triggered.connect(lambda: stacked_widget.setCurrentIndex(0))
    private_insurance_action.triggered.connect(lambda: stacked_widget.setCurrentIndex(1))

    annual_tax_menu.addAction(annual_tax_action)
    private_insurance_menu.addAction(private_insurance_action)
    menubar.addMenu(annual_tax_menu)
    menubar.addMenu(private_insurance_menu)
    main_window.setMenuBar(menubar)
    main_window.setCentralWidget(stacked_widget)

    app.aboutToQuit.connect(annual_timer.stop)
    app.aboutToQuit.connect(private_timer.stop)
    main_window.show()
    sys.exit(app.exec_())