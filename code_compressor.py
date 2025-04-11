def compress(text,print_vars=False,delete_newlines=False):
    text=" "+text

    exclude = ["function","return","end","getNumber","getBool","if","then","for","do","while","local",
               "else","elseif","and","or","not","in","onDraw","onDraw","onTick",
               "math","input","output","true","false","ipairs","httpReply",
               "type","table","nil",
               "screen","async","property","string"
               ]
    include = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
    includeNum = "0123456789"
    is_string = False

    variables = []
    counts = []

    print("\t",len(text),"initial characters")

    
    while text.count("--")>0:
        start = text.index("--")
        end = text.index("\n",start)
        text = text[:start]+text[end:]
        

    cur=""
    valid=True
    for i in text:
        
        
        if i in include or (i in includeNum and cur!=""):
            cur+=i
        else:
            if cur!="":
                if valid and (not cur in exclude) and (not is_string):
                    if (cur in variables):
                        counts[variables.index(cur)]+=1
                    else:
                        variables.append(cur)
                        counts.append(1)
                    
                cur=""
                valid=i!="."
                

        if i == '"':
            is_string = not is_string

    #print(variables)
    variables=[(counts[i],variables[i]) for i in range(len(variables))]
    variables.sort(reverse=True)
    if print_vars:
        variables = [variables[i]+(i,) for i in range(len(variables))]
        print(variables)
    variables=[i[1] for i in variables]
    print("\t",len(variables),"variables")
    replacements = []
    offset = 0

    for i in range(len(variables)):
        valid = False
        
        while not valid:
            pos = i+offset
            cur=""
            if pos>=len(include):
                cur += include[pos//len(include)-1]
            cur += include[pos%len(include)]
            if cur in exclude:
                offset += 1
            else:
                valid = True
            
        replacements.append(cur)

    #print(replacements)

    is_string = False

    cur=""
    for index in range(len(text)-1,-1,-1):
        i=text[index]
        
        
        if i in include or (i in includeNum):
            cur=i+cur
        else:
            if cur!="":
                valid=i!="."
                if valid and (not cur in exclude) and (not cur[0] in includeNum) and (not is_string):
                    text = text[:index+1] + replacements[variables.index(cur)] + text[index+len(cur)+1:]
                cur=""
                valid=True
        
        if i == '"':
            is_string = not is_string

    text = text.replace("\t","")

    valid = not delete_newlines
    while not valid:
        new = text.replace("\n\n","\n")
        valid = new == text
        text = new

    valid = False
    while not valid:
        new = text.replace(" \n","\n")
        valid = new == text
        text = new

    valid = False
    while not valid:
        new = text.replace("\n ","\n")
        valid = new == text
        text = new

    print("\t",len(text),"end characters")

    return text[1:]

if __name__ == '__main__':
    file = open("in.txt")
    text = file.read()
    file.close()

    text = compress(text)
    
    file = open("out.txt",mode="w", newline='\n')
    file.write(text)
    file.close()
