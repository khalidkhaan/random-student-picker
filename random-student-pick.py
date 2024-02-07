from io import StringIO, BytesIO
import random
import streamlit as st
import pandas as pd


def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data


def buildFinalStudentsList(givenNameIdDict, finalDistributedList):
    overAllDict = {}
    overAllDict.update(givenNameIdDict)
    for key in finalDistributedList:
        tempMarker = []
        tempVivaMark = []
        idList = finalDistributedList[key]
        for ids in overAllDict['ID']:
            if ids in idList:
                tempMarker.append(True)
                tempVivaMark.append(None)
            else:
                tempMarker.append(False)
                tempVivaMark.append(0)
        overAllDict[key] = tempMarker
        keyParam = key.split(': ')
        overAllDict[f'{keyParam[0][0]}{keyParam[1]} Mark'] = tempVivaMark
    overAllDict['Total Mark'] = None
    return overAllDict


st.header('Random viva candidate picker for the CSE110, CSE111, CSE220 & CSE221 courses of BRACU', divider='grey')

st.caption(''' 
- Upload the Attendance Sheet as CSV format.
- Provide how many viva you want to take for each students.
- Provide within how many lab classes you want to take those vivas.
- Click 'Generate the viva list' button and download the list in excel or csv format.
- Note: Download it if suitable, as you can't reproduce the same list.
''')
file = st.file_uploader("Download the Attendance Sheet as 'CSV' format and upload here")
if file is not None:
    inputDf = pd.read_csv(file)
    value_to_find = "ID"

    column_number = (inputDf.eq(value_to_find).any() == True).idxmax()
    foundId = False
    for colVal in inputDf[column_number]:
        if colVal == "ID":
            foundId = True
            break
    if column_number == "ID":
        foundId = True
    if not foundId:
        st.warning('Please upload a valid attendance sheet which contain the student ID.', icon="⚠️")
    else:
        nameColumn = (inputDf.eq('Name').any() == True).idxmax()
        nameIdDict = {}
        for indx, row in inputDf[[column_number, nameColumn]].iterrows():
            tempColumn = str(row[column_number])
            if tempColumn is not None and tempColumn != 'ID' and tempColumn != 'nan':
                nameIdDict[tempColumn] = row[nameColumn]
        newNameIdDict = {'ID': list(nameIdDict.keys()), 'Name': list(nameIdDict.values())}
        stringio = StringIO(file.getvalue().decode("utf-8"))
        string_data = stringio.read()
        givenIds = []
        for value in inputDf[column_number]:
            valStr = str(value)
            if len(valStr) == 8:
                givenIds.append(valStr)
        labDict = {}
        # initialEstimatedStudentPerLab = int(len(givenIds) * 0.5)

        eachViva = int(
            st.number_input("Enter how many vivas you want to take for each student:", min_value=1, max_value=4,
                            value=1, step=1))
        labDays = int(
            st.number_input("Enter in how many lab days you want to take those vivas:", min_value=eachViva,
                            max_value=10,
                            value=eachViva, step=1))
        initialEstimatedStudentPerLab = (eachViva * len(givenIds)) // labDays
        if st.button('Generate the viva list'):
            eachVivaEnsured = False
            eachStudentVivaCount = {}
            averagePerDayStudents = 0
            while not eachVivaEnsured:  # This loop to ensure minimum viva count for each students
                eachStudentVivaCount = {key: 0 for key in givenIds}
                averagePerDayStudents = 0
                for days in range(labDays):  # Distributing each student's id to lab days randomly
                    eachDaySet = set()
                    tempAllIds = list(givenIds)
                    for i in range(initialEstimatedStudentPerLab):
                        if len(tempAllIds) <= 0:
                            break
                        eachSelect = random.choice(tempAllIds)
                        isAvailable = True
                        while eachStudentVivaCount[eachSelect] >= eachViva:
                            tempAllIds.remove(eachSelect)
                            if len(tempAllIds) <= 0:
                                isAvailable = False
                                break
                            eachSelect = random.choice(tempAllIds)
                        if not isAvailable:
                            break
                        eachDaySet.add(eachSelect)
                        tempAllIds.remove(eachSelect)
                        eachStudentVivaCount[eachSelect] += 1
                    labDict[days] = eachDaySet
                    averagePerDayStudents += len(labDict[days])
                eachVivaEnsured = True
                for key in eachStudentVivaCount:
                    if eachStudentVivaCount[key] < eachViva:
                        eachVivaEnsured = False
                        initialEstimatedStudentPerLab += 1
                        break

            # averagePerDayStudents = averagePerDayStudents // labDays
            averagePerDayStudents = (eachViva * len(
                givenIds)) / labDays  # Calculating average distribution based on lab days not on the random distribution

            st.info(
                'Please download the list if you find suitable otherwise this combination will be lost. To generate different combination click "Geneate the viva list"')
            dictList = list(labDict.values())

            # Iterating from the behind for even distribution
            for indx in range(len(dictList) - 1, 0, -1):
                lenOfThatDay = len(dictList[indx])
                if lenOfThatDay < averagePerDayStudents:
                    for revIndx in range(indx - 1, -1, -1):
                        lenOfPrevDay = len(dictList[revIndx])
                        newSet = set()
                        if lenOfPrevDay > averagePerDayStudents:
                            for item in dictList[revIndx]:
                                if item not in dictList[indx]:
                                    dictList[indx].add(item)
                                    newSet.add(item)
                                    lenOfThatDay += 1
                                    if lenOfPrevDay - len(newSet) <= averagePerDayStudents:
                                        break
                                    if lenOfThatDay > averagePerDayStudents:
                                        break
                            for item in newSet:
                                dictList[revIndx].remove(item)


            # creating final distributed dictionary from the list
            finalDistributionDict = {}
            for indx in range(len(dictList)):
                finalDistributionDict[f'Viva: {indx + 1}'] = dictList[indx]
            max_length = max(len(values) for values in finalDistributionDict.values())
            finalDistributionDict = {
                key: list(values) + [None] * (max_length - len(values))
                for key, values in finalDistributionDict.items()
            }
            finalDictWithNameId = buildFinalStudentsList(newNameIdDict,finalDistributionDict)

            df = pd.DataFrame(finalDictWithNameId)
            st.dataframe(df, use_container_width=True, height=300)
            excel_file = to_excel(df)

            st.download_button(
                label="Download as Excel",
                data=excel_file,
                file_name="viva_list.xlsx",
                mime="application/vnd.ms-excel"
            )



footer = """<style>
a:link , a:visited{
color: grey;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: #FF4B4B;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: #262730;
color: grey;
text-align: center;
}
</style>
<div class="footer">
<p>Developed by <a style=' text-align: center;' href="https://cse.sds.bracu.ac.bd/faculty_profile/231/md_khaliduzzaman_khan_samrat" target="_blank">Md. Khaliduzzaman Khan Samrat</a></p>
</div>
"""
st.markdown(footer, unsafe_allow_html=True)
