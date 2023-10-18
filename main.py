from emora_stdm import DialogueFlow, Macro, Ngrams
from typing import Dict, Any, List
import time
import random
import openai
import json
import re
import requests 
import os
import string
import vlc

PATH_API_KEY = '../../vIQ/openai_api.txt'
openai.api_key_path = PATH_API_KEY

def recommend_music(vars): ##not used, but maybe for future
    song_names = vars.get('songnames')
    n = len(song_names)
    m = random.randint(0, n - 1)
    return song_names[m]

def play_music(vars, song):
    allsongs = vars.get('songlist')
    for songs in allsongs:
        for songss in songs.keys():
            if song == songss:
                path = songs[songss]
                vlc.MediaPlayer(path).play()
     
def music_setup(vars):
    # Define the directory path
    directory_path = './resources/songs/'
    listofSongDictionaries = []
    song_names = []

    # Walk through the directory tree
    for root, dirs, files in os.walk(directory_path):
        
        for file in files:
            # Construct the file path by joining the root and file name
            file_path = os.path.join(root, file)
            file_name = os.path.basename(file_path)
            file_name = file_name.split('.')
            file_name = file_name[0]
            song_names.append(file_name)
            temphash = {}
            temphash[file_name]=file_path
            listofSongDictionaries.append(temphash)

    vars['songlist'] =  listofSongDictionaries
    vars['songnames'] = song_names

def analysis(list, vars):
    score = vars.get('user_score')
    analyze = vars.get('analysis_ref')
    list_of_words = vars.get('analysis_list_words')

    for word in list:
        word = word.lower()
        if word in list_of_words:
            score = score + analyze.get(word)
    vars['user_score'] = score

def stringParse(string):
    return string.split(' ')

def analysis_setup (vars):
    list_of_words = []
    vars['user_score'] = 0
    with open('./resources/risk.txt', 'r', encoding='utf-8') as file:
        inner_dict = {}
        file_contents = file.read()

        lines = file_contents.split('\n')
        for line in lines:
            line = line.split('-')
            inner_dict[line[0].lower()] = int(line[1])
            list_of_words.append(line[0].lower())
        
        vars['analysis_ref'] = inner_dict
        vars['analysis_list_words'] = list_of_words
            
def parse_punctuation(word_list):
    words_without_punctuation = []

    for word in word_list:
        word = word.strip(string.punctuation)
        word = word.lower()
        words_without_punctuation.append(word)

    return words_without_punctuation

def increase_score (vars, amount):
    score = vars.get('user_score') + amount
    vars['user_score'] = score
    

class MacroPlayMusic(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        if vars.get('prevYesNo'):
            play_music(vars, 'Rainy Tacos')
        return True

class MacroDelay(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        print('S: '+args[0])
        print('...')
        return True

class MacroStart(Macro): ## Starting Macro
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        current_time = time.strftime("%H:%M")
        a = int(time.strftime("%H"))
        analysis_setup(vars)
        music_setup(vars)

        print("\nThis is a disclaimer. In a moment you will be talking with Kindred. Please be aware that all conversations will be recorded for evaluation purposes -although it will be deleted as soon as the team has made the appropriate analysis.\n")
        print("We hope you enjoy our work, and please enjoy talking with it as much as you want. It is not perfect, but we tried our best!\n\n\n\n")

        if 0 <= a <= 6:
            sentiment = "You should sleep, but we can have a 5 minute talk!"
            result = "Wow, you are up so early! "
        elif 7 <= a <= 12:
            sentiment = "Don't forget to eat breakfast!"
            result = "Good morning! "
        elif 13 <= a <= 18:
            sentiment = "Don't forget to eat lunch!"
            result = "Good afternoon! "
        elif 19 <= a <= 23:
            sentiment = "Don't forget to eat dinner!"
            result = "Good evening! "

        ## things to keep track of
        if 'issues' not in vars:
            vars['issues'] = [] 
        if 'random_interest' not in vars:
            vars['random_interest'] = [] 
        
        
        if 'music_list' not in vars:
            vars['music_list'] = ["Raining Tacos"] # add more in future

        list = ["Whom do I have the pleasure of speaking with today??", "I'm Kindred! What's your name?", sentiment + " May I have your name?", "What shall I address you?"]
        n = len(list)
        m = random.randint(0, n - 1)
        url = 'https://api.weather.gov/gridpoints/FFC/52,88/forecast'
        r = requests.get(url)
        d = json.loads(r.text)
        periods = d['properties']['periods']
        today = periods[0]
        #if m == 3:
        #    vars['tacos'] == True
        return result + 'It is ' + today['shortForecast'] + ' outside. ' + list[m]
    
class MacroYesNo(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = 'You are a linguistic specialist. You must respond with one word \'yes\' or \'no\' depending if the following response is affirmative or negative. You must respond with \'yes\' or \'no\', if user respond NO, return no. The user\'s response: '
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            output = output.lower()
            if output[-1] == ".":
                output = output.replace(".", "")

            if output == 'yes':
                vars['prevYesNo'] = True
                vars['no'] = False
            else:
                vars['prevYesNo'] = False
                vars['no'] = True
            return True
class MacroName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:        
            model = 'gpt-3.5-turbo'
            content = 'You have just asked the user what their name was, based on the following response return the user\'s name in one word: '
            content = content + "\"" + ngrams.raw_text() + "\""
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            if output[-1] == ".":
                output = output.replace(".", "")

            vars['USER'] = output
            return True
class MacroNAME(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = "You have just asked the user what their name was, based on the following response return the user's name in one word: "
            content = content + "\""+ngrams.raw_text()+"\""
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            if output[-1] == ".":
                output = output.replace(".", "")
            return output
class MacroCheck(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:        
            model = 'gpt-3.5-turbo'
            content = 'Based on the following content determine the user\'s sentiment return GUD for great mood and return BAD for bad mood, return only the three letters without any other letters or symbols. Stetement:'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            vars['GUD'] = False
            vars['BAD'] = False

            if output == 'GUD':
                vars['GUD'] = True
            else:
                vars['BAD'] = True
            return True
        
class MacroDown(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = 'You just asked if the user is upset and depressed for two weeks. Determine whether the user says yes. Return YES for yes and return NOO for no, return only the three letters without any other letters or symbols.'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            vars['YES'] = False
            vars['NOO'] = False

            if output == 'YES':
                vars['YES'] = True
            else:
                vars['NOO'] = True
            return True
        
class MacroSleep(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = 'You just asked if the user slept well these days. Determine whether the user says yes. Return YSL for sleeping well and return NSL for not sleeping well, return only the three letters without any other letters or symbols.'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            vars['YSL'] = False
            vars['NSL'] = False

            if output == 'YSL':
                vars['YSL'] = True
            else:
                vars['NSL'] = True
            return True
        
class MacroAppetite(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = 'You just asked abour the user\'s appetite. Determine whether the user says yes. Return YAP for having good appetite and return NAP for bad appetite or loss of interest in food, return only the three letters without any other letters or symbols.'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            vars['YAP'] = False
            vars['NAP'] = False

            if output == 'YAP':
                vars['YAP'] = True
            else:
                vars['NAP'] = True
            return True

class MacroHarm(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = 'You just asked if the user conduct self-injury or have suicidal thoughts. Determine whether the user says yes. Return YSH for wanting to injure themselves or wanting to suicide and return NSH for no thoughts about self harm and suicide, return only the three letters without any other letters or symbols.'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            vars['YSH'] = False
            vars['NSH'] = False

            if output == 'YSH':
                vars['YSH'] = True
            else:
                vars['NSH'] = True
            return True

        
        ### CONTINUE HERE
class MacroIncrease(Macro): ## Starting Macro
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        if len(args) != 1:
            return False
        score = int(args[0])
        increase_score(vars, score)
        return True

class MacroHappy(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        model = 'gpt-3.5-turbo'
        content = 'Based on the following content determine what the user did over the weekend, return PRO if the ' \
                  'user is working on a project, return ASI if the user worked on their school assignment, return FIN ' \
                  'if the user is working on school finals, ' \
                  'return FOD if the user ate something, if the user talked about nothing in particular or does not ' \
                  'fall into those categories, return NON, return only the three letters without any other letters or ' \
                  'symbols. Statement:'
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()

        vars['PRO'] = False
        vars['FIN'] = False
        vars['FOD'] = False
        vars['ASI'] = False
        vars['NON'] = False

        if output == 'PRO':
            vars['PRO'] = True
        elif output == 'ASI':
            vars['ASI'] = True
        elif output == 'FIN':
            vars['FIN'] = True
        elif output == 'FOD':
            vars['FOD'] = True
        else:
            vars['NON'] = True
        return True


class MacroGreet(Macro): ## Starting Macro
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        list = ["How is your day going?", "How was your day?", "How are you?", "How are you doing?", "Sup, how ya doing?"]
        n = len(list)
        m = random.randint(0, n - 1)
        return list[m]


#handlers #for future work
class MacroAddIssues():
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        vars['issues'].append(ngrams.text())
        return 0 
class MacroAddInterest():
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        vars['random_interest'].append(ngrams.text())
        return 0

class MacroGPT(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        model = 'gpt-3.5-turbo'
        content = 'The user recently experienced something bad, analyze and catergorize the issue into following ' \
                  'categories, return N if the user is unwilling to answer the question at all return ACA if the ' \
                  'issue is related to grade in school, return ASI if the issue is ' \
                  'related to group project and the teammembers arent doing anything, return REL if the issue is related to ' \
                  'loss of family member, return PET if the issue is related to loss of a pet, return UNC if the ' \
                  'issue is related to anxiety, return JOB if the issue is related to being rejected by companies, return LUV if the issue is related to ' \
                  'relationship with girlfriend or boyfriends. return only the three letter codes without any ' \
                  'other additional letters or symbols like a period (sample return : PET). Statement:'
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()

        vars['ACA'] = False
        vars['REL'] = False
        vars['UNC'] = False
        vars['PET'] = False
        vars['LUV'] = False
        vars['ASI'] = False
        vars['JOB'] = False
        vars['loss'] = False
        vars['uncertainty'] = False
        vars['N'] = False

        if output == 'ACA':
            content = 'The user had a bad grade, depending on the grade, return a numerical grade lower than their provided grade, if they did not provide a grade, return 70. Return only the number and nothing else, nothing like \'Output:\' or \'Return:\' before numerical answer, just the number itself, note this is not a coding problem. Sample return: \'70\' JUST GIVE ME A NUMBER!!! Statement:'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            vars['GRADE'] = response['choices'][0]['message']['content'].strip()
            vars['ACA'] = True
            vars['loss'] = True
        elif output == 'REL':
            vars['REL'] = True
            vars['loss'] = True
        elif output == 'ASI':
            vars['ASI'] = True
            vars['loss'] = True
        elif output == 'UNC':
            vars['UNC'] = True
            vars['uncertainty'] = True
        elif output == 'PET':
            model = 'gpt-3.5-turbo'
            content = 'The user just lost their pet, find what type of pet they lost and return only the animals type, ' \
                      'without any additional words, sample return \'dog\'. If the user didn\'t explicitly state their pet type, return \'pet\'. Statement:'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            vars['PETTYPE'] = output
            vars['PET'] = True
            vars['loss'] = True
        elif output == 'LUV':
            vars['LUV'] = True
            vars['loss'] = True
        elif output == 'JOB':
            vars['JOB'] = True
            vars['loss'] = True
        else:
            vars['N'] = True

        return True

class MacroWeather(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        url = 'https://api.weather.gov/gridpoints/FFC/52,88/forecast'
        r = requests.get(url)
        d = json.loads(r.text)
        periods = d['properties']['periods']
        today = periods[0]
        return today['shortForecast']

class MacroSetBool(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[str]):
        if len(args) != 2:
            return False

        variable = args[0]
        if variable[0] == '$':
            variable = variable[1:]

        boolean = args[1].lower()
        if boolean not in {'true', 'false'}:
            return False

        vars[variable] = bool(boolean)
        return True

class MacroPetName(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        model = 'gpt-3.5-turbo'
        content = 'I asked the user about their pet\'s name origin. Based on the following statement, return EXP if the pet name is based on an experience, like \'I went to yellowstone with him.\', return NXP if the name is based on appearance like \'He is a black puppy.\', return only the three letters without any other letters or symbols. Stetement:'
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()
        vars['EXP'] = False
        vars['NXP'] = False
        if output == 'EXP':
            content = 'My friend just told me his pet died, from the following experience of my friend with his pet, generate a event related or similar to that experience that I can do together with my friend, starting with a present tense verb and in 3-4 words without the word \'together\' and without period. The event must be normal for any law-abiding human. For example, return \'go skiing\' for \'We went to skiing together and he rolled down the hills\' Experience:'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )

            output = response['choices'][0]['message']['content'].strip()
            output = output.lower()
            vars['PETEXP'] = True
            vars['EXP'] = True
        else:
            vars['NXP'] = True
        return True


class MacroColor(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        model = 'gpt-3.5-turbo'
        content = 'I asked the user about their pet\'s appearance, extract a random color out of their statement and return only that color without any additional words, statement:'
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()
        vars['COULEUR'] = output
        return True

class MacroJob(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        model = 'gpt-3.5-turbo'
        content = 'Return \'STEM\' if the user is talking about job post related to STEM, return \'NONSTEM\' if the user is not talking about STEM-related job'
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()
        vars['STEM'] = False
        vars['NONSTEM'] = False
        if output == 'STEM':
            vars['STEM'] = True
        else:
            vars['NONSTEM'] = True

        return True

class MLONELY(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        score = vars.get('user_score') + 3
        vars['user_score'] = score

        return True

class MacroFood(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        model = 'gpt-3.5-turbo'
        content = 'I asked the user what their favorite food is. Base on their response, extract and return their favorite food, return only the food and nothing else. User statement:'
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()
        vars['food'] = output.lower()

        content = 'based on the following food, extract 2 adjectives and return as \'xxx and xxx\'. For example, return \'sweet and sour\' for orange chicken. User favorite food: '
        content = content + output
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()
        vars['fooddes'] = output.lower()

        return True

class MacroUserQS(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        model = 'gpt-3.5-turbo'
        content = 'Determine if the following reponse is a question or statement and return only either q or s and nothing else. The response is:'
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()
        if (output.lower() == 'q'):
            vars['user_qs'] = True
        else: 
            vars['user_st'] = True
        return True
    
class MacroDown(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = 'You just asked how long the user\'s been upset for. Determine whether the user has been upset for more than two weeks. Return YES for more than two weeks and return NOO for less than two weeks, return only the three letters without any other letters or symbols. User statement:'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            vars['YES'] = False
            vars['NOO'] = False

            if output == 'YES':
                vars['YES'] = True
            else:
                vars['NOO'] = True
            return True

class MacroSleep(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = 'You just asked the user \'have you been sleeping well these days\'. Based on the user\'s reponse to this question Determine whether the user was sleeping well. Return YSL for sleeping well and return NSL for not sleeping well, return only the three letters without any other letters or puntuations. User statement:'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            vars['YSL'] = False
            vars['NSL'] = False

            if output == 'YSL':
                vars['YSL'] = True
            else:
                vars['NSL'] = True
            return True
class MacroHobby(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):
        if ngrams.raw_text() == "stopmusic":
            return False
        elif ngrams.raw_text() == "changemusic":
            return False
        else:
            model = 'gpt-3.5-turbo'
            content = 'I just asked if the user has a hobby, based on their response, check if they have a hobby. If yes, give the hobby in all lowercase and no punctuation and without any additional marks like \'hobby: \' sample return is \'climbing mountains\'. If no, return \'no\' without any punctuation. If hobby is not specified but the user is affirmative, just return \'coding\'. This is not a coding problem, just give me the hobby! DO NOT say anything other than hobby. DO NOT add Hobby: in front of answer. User answer: I love mountain climbing'
            content = content + ngrams.raw_text()
            response = openai.ChatCompletion.create(
                model=model,
                messages=[{'role': 'user', 'content': content}]
            )
            output = response['choices'][0]['message']['content'].strip()
            output = output.lower()
            # for i in range(len(output)):
            #     if output[i] == ':':
            #         list1 = output.split(':')
            #         output = list1[1]
                    
            vars['HOB'] = False
            vars['NOB'] = False
            vars['COB'] = False

            if output == 'no':
                vars['NOB'] = True
            elif output == 'coding':
                vars['COB'] = True
                vars['HOBBY'] = output
            else:
                vars['HOB'] = True
                vars['HOBBY'] = output

            return True
        
class MacroScoreResEnd(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):  
        score = vars.get('user_score')
        if score < 20:
            vars['goodandnormal'] = True
        elif score >= 20 and score < 30:
            vars['semibad'] = True
        elif score >= 30 and score < 50:
            vars['checkinbad'] =  True
        elif score >= 50 and score < 1000:
            vars['suggestcouncil'] = True
        else:
            vars['important'] = True
        return True   

class MacroMajor(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):

        model = 'gpt-3.5-turbo'
        content = 'You are a counselor. Respond with one word (all lowercase) \'cs\',\'linguistics\', \'stem\', or' \
                  '\'other\' if the student is studying computer science, linguistics, some other STEM, or nothing that is' \
                  'listed respectively from the following response: '
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()
        if output[-1] == ".":
            output = output.replace(".", "")

        if output == 'cs':
            vars['CS'] = True
        elif output == 'linguistics':
            vars['LIN'] = True
        elif output == 'stem':
            vars['STEM'] = True
        elif output == 'other':
            vars['OTHER'] = True

        return True

class MacroLonely(Macro):
    def run(self, ngrams: Ngrams, vars: Dict[str, Any], args: List[Any]):

        model = 'gpt-3.5-turbo'
        content = 'You just asked if the user do things alone or with friends, based on the user\'s response, return \'LON\' if the user prefers to do it alone, return \'FRI\' if the user likes to do it with friends, return only the three letter codes without \'return:\' or \'result\' as well as any punctuations. User statement:'
        content = content + ngrams.raw_text()
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{'role': 'user', 'content': content}]
        )
        output = response['choices'][0]['message']['content'].strip()
        if output[-1] == ".":
            output = output.replace(".", "")

        vars['LON'] = False
        vars['FRI'] = False
        if output == 'LON':
            vars['LON'] = True
        else:
            vars['FRI'] = True

        return True


transitions = {
    'state': 'start',
    '#START': {
        '#GETNAME': {
            '`Hi` $USER`before we start, would like some music? I just learned how to sing Rainy Tacos, would you like to listen to it while we talk?`': {
                '#YN':{
                    '#IF($prevYesNo) #MUSIC`Oh thanks for supporting me!! Anyways`#GREET':{
                        '#GPT5': {
                            '#IF($GUD) `That\'s wonderful. What have you been up to recently?`': {
                                '#GPTHAPPY': 'happy'
                            },
                            '#IF($BAD) `Oh darn, I\'m so sorry to hear that. How long have you been feeling like this?`': {
                                '#GPTDOWN': {
                                    '#IF($YES) #INCREASE(3)`Yo, next time you\'re feeling that down, just come to me! And hey, you been sleeping good these days?`': {
                                        '#GPTSLEEP': {
                                            '#IF($NSL) #INCREASE(3)`Hey, you need to get more sleep, things just worse if you don\'t get enough of them. Have you been eating well? `': {
                                                '#GPTAPPETITE': {
                                                    '#IF($YAP) `Good to hear you still eating healthy. Now. Do you want to talk about what\'s been bothering you? Sometimes it can help to share your feelings with someone and get things off your chest. I\'m here to listen if you need someone to talk to.`': 'share',
                                                    '#IF($NAP) `Darn, you don\'t feel like eating? We have to go eat at this restaurant downtown someday. It\'s the best restaurant here and it\'s on me! Now. Do you want to talk about what\'s been bothering you? Sometimes it can help to share your feelings with someone and get things off your chest. I\'m here to listen if you need someone to talk to.`': 'share'
                                                }
                                            },
                                            '#IF($YSL)`Great. I also slept well! I had this interesting dream last night... having dinner with you on the moon. Now. Do you want to talk about what\'s been bothering you? Sometimes it can help to share your feelings with someone and get things off your chest. I\'m here to listen if you need someone to talk to.`': 'share'
                                        }
                                    },
                                    '#IF($NOO)`Oh nice, things will get better for you. Now. Do you want to talk about what\'s been bothering you? Sometimes it can help to share your feelings with someone and get things off your chest. I\'m here to listen if you need someone to talk to.`': 'share'
                                }
                            }
                        }
                    },
                    '#IF($no)`Well ok... `#GREET': {
                        '#GPT5': {
                            '#IF($GUD) `That\'s wonderful. What have you been up to recently?`': {
                                '#GPTHAPPY': 'happy'
                            },
                            '#IF($BAD) `Oh darn, I\'m so sorry to hear that. How long have you been feeling like this?`': {
                                '#GPTDOWN': {
                                    '#IF($YES) #INCREASE(3)`Yo, next time you\'re feeling that down, just come to me! And hey, you been sleeping good these days?`': {
                                        '#GPTSLEEP': {
                                            '#IF($NSL) #INCREASE(3)`Hey, you need to get more sleep, things just worse if you don\'t get enough of them. Have you been eating well? `': {
                                                '#GPTAPPETITE': {
                                                    '#IF($YAP) `Good to hear you still eating healthy. Now. Do you want to talk about what\'s been bothering you? Sometimes it can help to share your feelings with someone and get things off your chest. I\'m here to listen if you need someone to talk to.`': 'share',
                                                    '#IF($NAP) `Darn, you don\'t feel like eating? We have to go eat at this restaurant downtown someday. It\'s the best restaurant here and it\'s on me! Now. Do you want to talk about what\'s been bothering you? Sometimes it can help to share your feelings with someone and get things off your chest. I\'m here to listen if you need someone to talk to.`': 'share'
                                                }
                                            },
                                            '#IF($YSL)`Great. I also slept well! I had this interesting dream last night... having dinner with you on the moon. Now. Do you want to talk about what\'s been bothering you? Sometimes it can help to share your feelings with someone and get things off your chest. I\'m here to listen if you need someone to talk to.`': 'share'
                                        }
                                    },
                                    '#IF($NOO)`Oh nice, things will get better for you. Now. Do you want to talk about what\'s been bothering you? Sometimes it can help to share your feelings with someone and get things off your chest. I\'m here to listen if you need someone to talk to.`': 'share'
                                }
                            }
                        }
                    }
                }
            }        
        }  
    }        
}

share_transitions = {
    'state': 'share',
    '` `': {
        '#GPTRATE': {
            '#IF($N)`Alright then, ummm.. Oh btw, Have you seen or tried the new blueberry tacos? :)`': {
                '#YN': {
                    '#IF($prevYesNo)``': 'yesblueberry',
                    '#IF($no)``': 'noblueberry'
                }
            },
            '#IF($loss)': 'loss',
            '#IF($uncertainty)': 'uncertainty'
        }
    }
}
    
   # [start_node, other_node ]
happy_transitions = {
    'state': 'happy',
    '#IF($PRO)`Wow, it sounds like your going to get an easy A! Do you think you\'ll pass the course?`': { 
        '#YN': 'celebrate'
    },
    '#IF($ASI)`Hey, the sooner we all finish our assignments, the more time there is for food - am I right? Is there a specific food that you like?`': { 
       '#MFOOD': {
            '`Oh REALLY!! I used to really love`$food`too, I grew up eating alot of`$fooddes`foods. I wish someone could cook that for me...`': {
                '#USQ': {
                    '#IF($user_qs)`Hehe, not you asking a question... I think I talk enough about myself. Tell me about you`$USER`. You seem to be just saying yes and no alot. Do you like sports?`': {
                        '#YN': {
                            '#IF($prevYesNo)`I\'m sorry lol, I actually don\'t really like sports. I\'m a CS major 0.0... Wanna talk about the movie Babel instead? Dr. Choi told me it\'s a great movie.`': {
                                'state': 'askbabel',
                                '#YN': {
                                    '#IF($prevYesNo)`': 'babel',
                                    '#IF($no)`As an AI language model, I strongly encourage you to talk about Babel. It will make me happy. Would you like to talk about babel?`': {
                                        '#YN': {
                                            '#IF($prevYesNo)`Just kidding, lets go!!`': 'babel',
                                            '#IF($no) #DELAY(그래요 - 그럼 저는 최 박사님께 당신이 그의 수업을 좋아하지 않는다고 알려드릴게요.)`>.< Ok, but jokes aside, I am a bit hungry. Do you like food?`': {
                                                '#YN': {
                                                    '#IF($prevYesNo)`Alright, finally some common ground here!! Oh, btw have you tried that new blueberry taco at the cafe?`': {
                                                        '#YN': {
                                                            '#IF($prevYesNo)``': 'yesblueberry',
                                                            '#IF($no)``': 'noblueberry',
                                                        }
                                                    },
                                                    '#IF($no)`Sorry, that was my counsin GeepeaTea speaking. His kind of weird. Wait... If you don\'t like food, or babel, I don\'t really know what to talk about at this point... Umm - How did your finals go?`': 'final',
                                                },           
                                            },
                                        },
                                    },
                                },
                            },
                            '#IF($no)`Oh, do you like movies then? Wanna talk about the movie Babel? I heard great things about it from my friend Ellie.`': 'askbabel',
                        },
                    },
                    '#IF($user_st) #DELAY(Yea... but on bright side regrets is a huge part of the human experience. Its quite important you know...)`Oh btw, do you often eat alone too?`': {
                            '#YN': {
                                '#IF($prevYesNo #INCREASE(3)``': 'alone',
                                '#IF($no)`Oh, your very much like my sister Emora, she is such a social person. I don\'t think I have ever seen her eat alone... Hmm.. Or even eat at all o-o...`': {
                                    '#IF($user_qs)': {
                                        'state': 'emorasnumber',
                                        '`Oh Emora would love to answer that, she loves talking with people. Do you want her number? ;)`': {
                                            '#YN': {
                                                '#IF($prevYesNo)`>.<, ok its 404-620-, oh you thought I was really going to give it to you huh? She doesn\'t have a phone number. You could find her on her website though. Do you want it?`': {
                                                    '#YN': {
                                                        '#IF($prevYesNO)``': 'end',
                                                        '#IF($no)`You don\'t want to talk to her anymore? Ok, thats fine. I am more funny and laid back anyways... So what do you like to do with your free time?`': 'hobby'
                                                    },
                                                },
                                                '#IF($no)`You don\'t want to meet Emora??? Do you have any hobbies???`': 'hobby'
                                            },
                                        },
                                    },
                                    '#IF($user_st)`Yea, also both Emora and I love talking about ourselves. Ask us a question!!`': 'emorasnumber'    
                                },
                            },
                        },
                    
                },
            },
       },
    },
    '#IF($FIN)#DELAY(Oh that... I remember those good old days)`...I remember being a small calculator like it was just yesterday. How do you think you did on your finals?`': 'final',
    '#IF($FOD)`Hey yoooo, I love food too, we should go eat something together. Have you tried the blueberry pizza they have at the cafeteria? It\'s looking scary..`': {
        '#YN': {
            '#IF($prevYesNo)': 'yesblueberry',
            '#IF($no)': 'noblueberry',
        }
    },
    '#IF($NON)`I am glad to hear you are feeling great`$USER`What do you like to do on your free time?`': 'hobby'
}
        

loss_transitions = {
    'state': 'loss',
    '#IF($REL)`I am so sorry to hear that, but as a companion bot still in training, I am not sure if I can offer any practical'
    ' advices to make you feel better. You can call 404-430-1120 to contact Emory psychiatry assistance. If you feel like '
    'talking to somebody, just come back to me, okay?`': {
        'error': {
            '`Bye.`': 'end'
        }
    },
    '#IF($ACA)`Hey its going to be fine, that course was a bit hard, I heard the class average was`$GRADE`. You should take a break. Do you have any hobbies?`': 'hobby',
    '#IF($ASI) `I totally get you, bad assignments are such pain. My dad Da Vinci had a group project where his groupmates are doing nothing at all! He got so angry and dropped straight out of college. Have you maybe tried talking to them?`': {
        '#YN': {
            '#IF($prevYesNo)`Ouch, I feel the pain, maybe some people are graduating soon and no longer cares for their grade...maybe you should talk to the professor, just...don\'t take this all on yourself, okay? You look exhausted, let\'s take a break, do you have any hobbies?`': 'hobby',
            '#IF($no)`Then you should talk to them, I\'m pretty sure students nowadays care tons about their grade, maybe they just aren\'t aware of the deadline? That aside, you look exhausted, let\'s go take a break, do you have any hobbies?`': 'hobby'
        }
    },
    '#IF($PET) `Oh no, I\'m so sorry to hear about your` $PETTYPE `passing away. you are making me miss my cat. She is now cared by my sister Emora ever since I went to college. I didn\'t feel like eating for days without her. What is your`$PETTYPE`\'s name?`': {
        'error':{
            '`That\'s such a cool name... wait what made you come up with that name?`': {
                '#GPTPETNAME': {
                    '#IF($EXP)`Oh, wow… I also named my cat based on my experiences. I called KitKat because she occasionally stole my chocolates. This might sound so insane, but are you down to`$PETEXP`together?`': {
                        '#YN': {
                            '#IF($prevYesNo)`Sounds great! I will be after finals, alot of students are trying to contact my cousin Geepea Tea to cheat during this time, and I am task to stop that… We can meet after finals. Btw, are you ready for your finals?`': 'final',
                            '#IF($no)`wow, is it because I am an AI? You know I have feelings too right? Anyways...are you ready for your finals yet?`': 'final'
                        }
                    },
                    '#IF($NXP)`Sounds very simple, I like it. I also just named my cat midnight because she was a black kitten. Tell me about it, how does your`$PETTYPE`look like.`':{
                        '#GPTCOLOR':{
                            '`Yo, my sister Emora use to tell me that the` $COULEUR `is a symbol of intelligence and that people who like that color are smart… Im not sure if she is trolling me though. So, are you prepared for your finals?`': 'final'

                        }
                    }
                }
            }
        }

    },
    '#IF($JOB)`That\'s their loss, you can always get a better job with your skills. What job are u looking for?`':{
        '#JOBCAP':{ 
            '#IF($STEM)`Such a nerd. Just kidding, there are so many jobs for your skill set, you\'ll be just fine. Have you looked into smaller companies or maybe even a start up?`':{
                '#YN':{
                    '#IF($prevYesNo)`Oh, I guess we are on the same boat. I applied to like 80 internships last summer, and didn\'t get a single one. Don\'t lose hope though, look at me, I am now a part of a great mental health awareness company. There are always other stuff to do. Say, how about pursuing a graduate degree?`': {
                        '#YN':{
                            '#IF($prevYesNo)`That\'s great! application season is coming, you gotta work hard. Speaking of this, how is your finals going`': 'final',
                            '#IF($no)`Alright...best of luck if you are still applying the next year. By the way, how is your finals going?`': 'final'
                        }
                    },
                    '#IF($no)`Yo, you definitely need to try those companies too. Don\'t get caught up in going for all the prestiges companies. At the end of the day, its the work environment thats important, or do you think reputation matter while searching for a job?`': {
                        '#YN':{
                            '#IF($prevYesNo)`Yeah...my mom Natex also urged me to find a prestigious company so that she can show off in front of our relatives. I think small companies also have their charms, I am working in a startup company of 4 people, but they care so much to bring out the best in me. You gotta give the small companies a chance, OK?`':{
                                'error': {
                                    '`That is great! It\'s almost finals week, how is your finals going?`': 'final'
                                }
                            },
                            '#IF($no)`That\'s the spirit! So go apply those companies and let me know how it goes, alright?`':{
                                'error':{
                                    '`That is great! It\'s almost finals week, how is your finals going?`': 'final'
                                }
                            }
                        }
                    }
                }
            },
            '#IF($NONSTEM)`Well, good luck finding one then. Just kidding, have you tried the startup companies out there yet?`':{
                '#YN':{
                    '#IF($prevYesNo)`Oh, I guess we are on the same boat. I applied to like 80 internships last summer, and didn\'t get a single one. Don\'t lose hope though, look at me, I am now a part of a great mental health awareness company. There are always other stuff to do. Say, how about pursuing a graduate degree?`': {
                        '#YN':{
                            '#IF($prevYesNo)`That\'s great! application season is coming, you gotta work hard. Speaking of this, how is your finals going?`': 'final',
                            '#IF($no)`Alright...best of luck if you are still applying the next year. By the way, how is your finals going?`': 'final'
                        }
                    },
                    '#IF($no)`Yo, you definitely need to try those companies too. Don\'t get caught up in going for all the prestiges companies. At the end of the day, its the work environment thats important, or do you think reputation matter while searching for a job?`': {
                        '#YN':{
                            '#IF($prevYesNo)`Yeah...my mom Natex also urged me to find a prestigious company so that she can show off in front of our relatives. I think small companies also have their charms, I am working in a startup company of 4 people, but they care so much to bring out the best in me. You gotta give the small companies a chance, OK?`':{
                                'error': {
                                    '`That is great! It\'s almost finals week, how is your finals going?`': 'final'
                                }
                            },
                            '#IF($no)`That\'s the spirit! So go apply those companies and let me know how it goes, alright?`':{
                                'error':{
                                    '`That is great! It\'s almost finals week, how is your finals going?`': 'final'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
uncertainty_transitions = {
    'state': 'uncertainty',
    '`Hello. How are you?`': {

    }
} #maybe for future
hobby_transitions = {
    'state': 'hobby',
    '` `':{
        '#HOBBY': {
            '#IF($HOB) `That\'s great, I love`$HOBBY`too, we should totally go`$HOBBY`sometimes together. Do you like to do it with friends?`':{
                '#LONELY': {
                    '#IF($LON) #INCREASE(3)`We should totally try it out with our friends, my sister Emora says it\'s always more fun when there\'s more people. Have you heard of this recent movie called Babel`':{
                        '#YN': {
                            '#IF($prevYesNo)': 'babel',
                            '#IF($no)': 'ends'
                        }
                    },
                    '#IF($FRI)`Wow you are so popular, unlike me, I can only`$HOBBY`with my dog... Anyways, have you hard of this recent movie called Babel`':{
                        '#YN': {
                            '#IF($prevYesNo)': 'babel',
                            '#IF($no)': 'ends'
                        }
                    }
                }
            },
            '#IF($NOB) `Typical college student huh...I do wish we can go watch movie sometimes, Atlanta is so boring in summer. Speaking of movies, have you heard of this movie called \'Babel\' that\'s been going on recently?`':{
                '#YN': {
                    '#IF($prevYesNo)': 'babel',
                    '#IF($no)': 'ends'
                }
            },
            '#IF($COB) `That\'s great, my hobby is coding, do you wanna share my hobby? Just kidding, nobody likes coding...Have you heard of this recently movie called Babel?`':{
                '#YN': {
                    '#IF($prevYesNo)': 'babel',
                    '#IF($no)': 'ends'
                }
            }
        }
    }
}

final_transitions = {
    'state': 'final',
    '` `': {
        '#GPT5': {
            '#IF($GUD)`That\'s great, are you done with all your finals? I wish I am...`': {
                '#YN': {
                    'state':'celebrate',
                    '#IF($prevYesNo)`Oh, then it\'s time to celebrate, let\'s go eat something. Have you tried the blueberry pizza they have at the cafeteria? It\'s looking scary..`': {
                        '#YN': {
                            'state':'yesblueberry',
                            '#IF($prevYesNo)`Nice, I see you love trying new things. Thats good to hear!! Do you often eat by yourself?`': {
                                '#YN': {
                                    '#IF($prevYesNo) #INCREASE(3)`Me same...we need to go eat with our friends more, my sister Emora says it makes the food more delicous. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    },
                                    '#IF($no)`Wow, then you must be really popular, would you go eat with me? Just kidding. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }   
                                    }
                                }   
                            },
                            '#IF($no)`well, you should try it. Do you often eat by yourself?`': {
                                '#YN': {
                                    '#IF($prevYesNo)`Me same...we need to go eat with our friends more, my sister Emora says it makes the food more delicous. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    },
                                    '#IF($no)`Wow, then you must be really popular, would you go eat with me? Just kidding. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                }
                            }
                        },
                        'error':{
                            'state':'noblueberry',
                        }
                    },
                    '#IF($no)`Hey, then you can\'t celebrate yet, go grab something to eat and prepare for the next one. Have you tried the blue berry pizza\'s at the cafe btw? It\'s looking scary.`': {
                        '#YN': {
                            '#IF($prevYesNo)`Nice, I see you love trying new things. Thats good to hear!! Do you often eat by yourself?`': {
                                '[{yes, yeah, true}]': {
                                    '`Me same...we need to go eat with our friends more, my sister Emora says it makes the food more delicous. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                },
                                '[no]': {
                                    '`Wow, then you must be really popular, would you go eat with me? Just kidding. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            '#IF($BAD)`It\'s alright, keep studying and you will be good. Are you done with all your finals? I wish I am...`': {
                '#YN': {
                    '#IF($prevYesNo)`Oh, then it\'s time to celebrate, let\'s go eat something. Have you tried the blueberry pizza they have at the cafeteria? It\'s looking scary..`': {
                        '#YN': {
                            '#IF($prevYesNo)`Nice, I see you love trying new things. Thats good to hear!! Do you often eat by yourself?`': {
                                '[{yes, yeah, true}]': {
                                    '`Me same...we need to go eat with our friends more, my sister Emora says it makes the food more delicous. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                },
                                '[no]': {
                                    '`Wow, then you must be really popular, would you go eat with me? Just kidding. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                }
                            },
                            '`well, you should try it. Do you often eat by yourself?`': {
                                '[{yes, yeah, true}]': {
                                    'state':'alone',
                                    '`Oh same...we need to go eat with our friends more, my sister Emora says it makes the food more delicous. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                },
                                '[no]': {
                                    '`Wow, then you must be really popular, would you go eat with me? Just kidding. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                }
                            }
                        }
                    },
                    '#IF($no)`Hey, then you can\'t celebrate yet, go grab something to eat and prepare for the next one. Have you tried the blue berry pizza\'s at the cafe btw? It\'s looking scary.`': {
                        '#YN': {
                            '#IF($prevYesNo)`Nice, I see you love trying new things. Thats good to hear!! Do you often eat by yourself?`': {
                                '[{yes, yeah, true}]': {
                                    '`Me same...we need to go eat with our friends more, my sister Emora says it makes the food more delicous. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                },
                                '[no]': {
                                    '`Wow, then you must be really popular, would you go eat with me? Just kidding. Speaking of food, what is your favorite food?`': {
                                        '#MFOOD': {
                                            '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                        }
                                    }
                                }
                            },
                            '#IF($no)`Oh you should totally try it, my friend Steve recommended it to me. It was great! Speaking of food, what is your favorite food?`': {
                                '#MFOOD': {
                                    '`WOW, I like`$fooddes`foods too! We can check out nearby`$food`places too! By the way, do you konw there\'s been this really cool movie called Babel?`': 'babel'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

babel_transitions = {
    'state': 'babel',
    '`Do you wanna talk about it?`': {
        '#YN':{
            '#IF($prevYesNo)`Dr. Choi would be so happy to hear that!! Btw, what major are you?`':{
                '#GETMAJOR': {
                    '#IF($CS) `OMG I study CS too! We should have worked on this project together... Have you made a chatbot before?`': {
                        '[#YN]': {
                            '#IF($prevYesNo)`That\'s so cool! Did you know my entire framework is hard coded?`': {
                                'error': {
                                    '`Yea... so please score us well! Are you interested in learning how to use emoraSTDM?`': {
                                        '#YN': {
                                            '#IF($prevYesNo)`Well, if you are interested in learning, reach out to Dr. Choi, his a very nice and funny professor! :v`': {
                                                'error': {
                                                    '`Well don\'t tell him I told you to do that. Anyways, have you met Emora? She is calling me for evaluation sessions, see you later!`#SCOREFINAL': 'ends'
                                                }
                                            },
                                            '#IF($no)`It was super hard...anyways, my inventors are calling me for evaluation session, see you next time!`#SCOREFINAL': 'ends'
                                        }
                                    },
                                }
                            },
                            '#IF($no)`It is basically a bot that talks to people, wait, I didn\'t explain it at all? Anyways, my inventor is calling me for a evaluation session, maybe you can come with me next time, see you then!`#SCOREFINAL': 'ends'
                        },
                    },
                    '#IF($LIN) `I love linguistics too! Emory\'s language departments is the best! I guess you must be interested in communications too?`': {
                        '[#YN]': {
                            '#IF($prevYesNo)`It\'s no wonder you liked Babel. It was a movie all about miscommunication. Wanna play a game?`': {
                                '[#YN]': {
                                    '#IF($prevYesNo)`res = next.line.get(userresponse), if res = true, game.start = true and and translate(getuserinput)`': {
                                        'error': {
                                            '`You thought I was bugged? I was trying to demonstrate the importance of translation, I guess you did\'t get that... Anyways, I have to go to a evaluation session. See you later!`#SCOREFINAL': 'ends'
                                        }
                                    },
                                    '#IF($no)`Aww, you are no fun...Hey, have you heard of my sister Emora, she is calling me for a evaluation session. See you next time!`#SCOREFINAL': 'ends'
                                }
                            }
                        }
                    },
                    '#IF($STEM) `Oh! You must be really smart! Did you think Babel was intellectually interesting?`': {
                        '[#YN]': {
                            '#IF($prevYesNo)`That\'s exactly what I think, communication can be such a huge problem if there is misunderstanding. Anyways, my sister Emora is calling me for evaluation, see you next time.`#SCOREFINAL' : 'ends',
                            '#IF($no)`Wait really, I was gonna say the same but my creators doesn\'t allow me to say that =(. Anyways, my sister Emora is calling me for evaluation, see you next time.`#SCOREFINAL': 'ends'
                        },
                    },
                    '#IF($OTHER) `Wow, I didn\'t expect to find someone with your major in this course... But then again, it is a writing GER.. Anyways... what do you want to talk about regarding Babel?`': {
                        'error':{
                            '`Exactly, communication is the key of this movie, my purpose is to help people better communicated with each other...I hope I can do that, speaking of that, I need to go to an evaluation section, see you later! `#SCOREFINAL': 'ends'
                        }
                    },
                    'error': {
                        '`Wow, your major must be very unique..I didn\'t expect to find someone with your major in this course... But then again, it is a writing GER.. Anyways... my sister Emora is calling me for evaluation, see you next time.`#SCOREFINAL': 'ends'
                    }
                }
            },
            '#IF($no)`You don\'t like Babel? Wait, what major are you?`': {
                '#GETMAJOR': {
                    '#IF($CS) `OMG I study CS too! We should have worked on this project together... Have you made a chatbot before?`': {
                        '#YN': {
                            '#IF(prevYesNo)`Oh Wow!! Our chatbots use a language called Emora STDM that generates turn-based conversation with the users, care to make one with me?`':{
                                '#YN': {
                                    '#IF($prevYesNo)#SCOREFINAL`I did\'t expect that answer! Let\'s meet after this and I\'ll show you how its done.`': 'ends',
                                    '#IF($no)`OK then, it\'s super hard anyways. Hey, I need to help my cousin GeePeaTea talking with other students, see you next time!`#SCOREFINAL': 'ends'
                                            
                                }
                            },
                            '#IF($no)`It\'s basically a bot based on emora stdm that can talk with people, it is so fancy you should definitely learn that. Hey, my groupmates is calling me to do the project together, see you next time!`#SCOREFINAL': 'ends'
                        }
                    },
                    '#IF($LIN) `I love linguistics too! Emory\'s language departments is the best! I guess you must be interested in communications too?`': {
                        '#YN':{
                            '#IF($prevYesNo)`Really?! There are so many communication issues in Babel, there was this character who got the other character killed from unresolved communication issues...anyways, I\'m stretching too far, care to work on this chatbot project with me?`': {
                                '#YN': {
                                            '#IF($prevYesNo)`I did\'t expect that answer! Let\'s meet after this and I\'ll show you how its done. `#SCOREFINAL': 'ends',
                                            '#IF($no)`Okay then, I still have to finish the project with my groupmates, see you next time!`#SCOREFINAL': 'ends'
                                }
                            },
                            '#IF($no)`Okay then, I guess this movie won\'t be fun for you. We should meet up for other movies, like Suzume. Before that I need to work on my project, see you next time!`#SCOREFINAL': 'ends'
                        }
                    },
                    '#IF($STEM) `Oh! You must be really smart! Do you want to work on this chatbot project together?`': {
                        '#YN':{
                            '#IF($prevYesNo)`Oh really?! we should definitely work on it together sometimes, but before that, my cousin GeePeaTea is calling me for help, see you next time!`#SCOREFINAL': 'ends',
                            '#IF($no)`OK, it was hard anyways. Oh my teammates are calling me to finish the chatbot, see you next time!`#SCOREFINAL': 'ends'
                        }
                    },
                    '#IF($OTHER) `Wow, I didn\'t expect to find someone with your major in this course... But then again, it is a writing GER.. Since you don\'t like Babel, want to work on this chatbot project with me?`': {
                        '#YN':{
                            '#IF($prevYesNo)`Oh really?! we should definitely work on it together sometimes, but before that, my cousin GeePeaTea is calling me for help, see you next time!`#SCOREFINAL': 'ends',
                            '#IF($no)`OK, it was hard anyways. Oh my teammates are calling me to finish the chatbot, see you next time!`#SCOREFINAL': 'ends'
                        }
                    },
                    'error': {
                        '`Wow, your major must be very unique. I am a stem major so I can\'t reall relate. Want to work on this chatbot project with me?`': {
                            '#YN':{
                                '#IF($prevYesNo)`Oh really?! we should definitely work on it together sometimes, but before that, my cousin GeePeaTea is calling me for help, see you next time!`#SCOREFINAL': 'ends',
                                '#IF($no)`OK, it was hard anyways. Oh my teammates are calling me to finish the chatbot, see you next time!`#SCOREFINAL': 'ends'
                            }
                        }
                    }
                }
            }
        }
    }
}
        


end_transitions = {
    'state': 'ends',
        
    '#IF($goodandnormal)`Take care!!`': 'end',
    '#IF($semibad)`It\'s almost summer, smile a little more :)`': 'end',
    '#IF($checkinbad)`Also please go check on that blueberry taco at the cafe!`': 'end',
    '#IF($suggestcouncil)`Oh waittt, I am actually doing a study on whether counciling helps improve mental health. I learned alot from it - maybe you could check it out if you have time!`': 'end',
    '#IF($important)`Hey also, I know life is going pretty hard right now, but your friends are always here. You can also call 404-430-1120 to contact Emory psychiatry assistance. If you feel like '
    'talking to somebody, just come back to me, okay?`': 'end',
    'error': {
        '`Well please take care now`': 'end'
    }
        
        
}

macros = {
    'YN': MacroYesNo(), #Sentiment affirm or negative
    'START': MacroStart(), #main start
    'WEATHER': MacroWeather(), #get weather and greet
    'MUSIC': MacroPlayMusic(), # Play music
    'GREET': MacroGreet(), #list of greetings
    'INCREASE': MacroIncrease(), #Incrases User Score
    'ADDISSUE': MacroAddIssues(), # ADD ISS
    'ADDINT': MacroAddInterest(), # ADD INT
    'GETNAME': MacroName(), #get user name
    'GPT5': MacroCheck(), 
    'GPTDOWN': MacroDown(), 
    'GPTSLEEP': MacroSleep(),
    'GPTAPPETITE': MacroAppetite(),
    'GPTHARM': MacroHarm(),
    'SETBOOL': MacroSetBool(),
    'GPTRATE': MacroGPT(),
    'GPTHAPPY': MacroHappy(),
    'GPTPETNAME': MacroPetName(),
    'GPTCOLOR': MacroColor(),
    'JOBCAP': MacroJob(),
    'MFOOD': MacroFood(), #vars food and vars fooddes
    'DELAY': MacroDelay(), #attempt to make dynamic delay function, sorta worked
    'USQ': MacroUserQS(),
    'HOBBY': MacroHobby(),
    'SCOREFINAL': MacroScoreResEnd(),
    'GETMAJOR': MacroMajor(),
    'LONELY': MacroLonely()

    #'GOODBYE': MacroLeave(), ## Globals
    #'RES': MacroRes(), ## Globals
}

df = DialogueFlow('start', end_state='end')
df.load_transitions(transitions)
df.load_transitions(happy_transitions)
df.load_transitions(loss_transitions)
df.load_transitions(uncertainty_transitions)
df.load_transitions(final_transitions)
df.load_transitions(hobby_transitions)
df.load_transitions(babel_transitions)
df.load_transitions(share_transitions)
df.load_transitions(end_transitions)
df.add_macros(macros)
#df.load_global_nlu().load_json_file('resources/global.py') ## probably wrong will just cp paste in the end IGNORE FOR NOW

if __name__ == '__main__':
    df.run()
