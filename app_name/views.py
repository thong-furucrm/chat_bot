import json
from django.shortcuts import render
import openai
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
import os
import unicodedata
from unidecode import unidecode

load_dotenv()
api_key = os.environ.get('OPENAI_API_KEY')


def format_url(url):
    url = unicodedata.normalize('NFKD', url).encode(
        'ASCII', 'ignore').decode('utf-8')
    url = url.replace(" ", "-")
    return url


def generate_question_and_answer(question):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": question}],
        max_tokens=193,
        temperature=0,
        api_key=api_key
    )
    answer = response.choices[0].message.content
    answer = unidecode(answer)
    return answer


@csrf_exempt
def demo(request):
    print('----------------- call demo function --------------------')
    if request.method == 'POST':
        # Get request
        question = json.loads(request.body).get('question')
        medicines = json.loads(request.body).get('medicines')

        try:
            # Lower case question
            analyzer_question = analyze_question(question)
            medicine_table = analyzer_question['table']
            medicine_name = analyzer_question['medicineName'].lower()
            print(f"bbb: {medicine_name}")
            print(f"bbb: {medicine_table}")

            # Get all data title in Knowledge base
            medicines_title = [item['Title'] for item in medicines]
            print(f"b: {medicines_title}")

            default_url = 'https://crm94-dev-ed.develop.my.site.com/pharma/s/article/'
            response = ''

            # Check medicine_name if exits
            if medicine_name in medicines_title:
                if medicine_name and analyzer_question['table'] == 'thuốc':
                    response = format_url(default_url+medicine_name)
                elif medicine_name and analyzer_question['table'] == 'giá bán thuốc':
                    response = format_url(default_url+medicine_table+' '+medicine_name)
                elif medicine_name and analyzer_question['table'] == 'quy trình sản xuất':
                    response = format_url(default_url+medicine_table+' '+medicine_name)
                else:
                    response = generate_question_and_answer(question)
            else:
                response = 'Chúng tôi không có loại thuốc này'

            # json_string = json.dumps(analyze_question)
            # result_dict = json.loads(json_string)
            # print(type(result_dict))

            # print(analyzer_question["table"])
            # print(analyzer_question["medicine_name"])
            # prompt = question
            # model_name = 'davinci:ft-huan-eth:training-file-stop-sequences-2023-10-04-08-47-11'
            # response = openai.Completion.create(
            #     engine=model_name,
            #     prompt=prompt,
            #     max_tokens=100,
            #     stop='END'
            # )
            # print(f'-------------------answer is : {response.choices[0].text}')

            # return HttpResponse(response.choices[0].text)
            return HttpResponse(response)
        except Exception as e:
            print(f'Lỗi không lấy được medicine_name hoặc medicine_table: {e}')
            return HttpResponse("Vui lòng cung cấp câu hỏi rõ hơn.")
    return render(request, 'index.html')


def analyze_question(question):
    template = '{"table": "", "medicineName": ""}'
    name_table = 'thuốc, giá bán thuốc, quy trình sản xuất, chào hỏi'
    prompt = f"""The statement: "{question}".
                Analyze the statement above to determine if it closely matches any category listed below:
                (keyCategory: category name)
                {name_table}
                Return with format {template}. No explanation
                NOTE:
                - medicineName is the name of the medicine. Check if the sentence you are analyzing has a question about medicine, otherwise return null
                - keyCategory is the keyCategory above of the most suitable category for the statement. If there is no matching category, please return null"""
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500,
        n=1,
        stop=".",
        temperature=0,
        api_key=api_key
    )
    label = response.choices[0].text.strip()
    result_dict = json.loads(label)
    return {"table": result_dict['table'], "medicineName": result_dict['medicineName']}
