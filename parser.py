import xml.etree.ElementTree as ET
import PyV8

class Parser(object):
    """Parses a VXML document while processing it."""
    def __init__(self, file, io):
        self.filename = file
        self.et = ET.parse(file)
        self.root = self.et.getroot()
        self.scripts = self.root.findall('script')
        self.ctxt = PyV8.JSContext()
        self.ctxt.enter()
        for s in self.scripts:
            self.ctxt.eval(s.text)
        self.form = self.root.find('form')
        self.io = io
        self.fields = dict()

    def walk(self):
        for element in self.form:
            if element.tag == 'block':
                self.processBlock(element)
            elif element.tag == 'field':
                self.processField(element)

    def processBlock(self, element):
        iter = element.itertext()
        text = iter.next() + ' '
        for expr in element:
            text += self.interpret(expr.attrib['expr'])
        try:           
            text += iter.next() + ' '
        except:
            pass #TODO: Add logging
        finally:
            self.io.output(text)

    def interpret(self, src):
        for k, v in self.fields.iteritems():
            src = src.replace(k, "'" + v + "'")
        return str(self.ctxt.eval(src))

    def processField(self, element):
        field = element.attrib['name']
        value = ''
        for child in element:
            if child.tag == 'prompt':
                self.processPrompt(child)
            elif child.tag == 'grammar':
               value = self.processGrammar(child)
            elif child.tag == 'filled':
                self.processFilled(child, value) 
        self.fields[field] = value

    def processPrompt(self, element):
        iter = element.itertext()
        text = iter.next() + ' '
        vars = [c.attrib['expr'] for c in element]
        for v in vars:
            text += self.fields[v] + ' '               
        try:
            while True:
                text += iter.next() + ' '
        except:
            pass
        finally:
            self.io.output(text)

    def processGrammar(self, grammar):
        rootID = grammar.attrib['root'];
        rules = dict()
        for rule in grammar:
            rules[rule.attrib['id']] = Rule(rule)
        root = rules[rootID]
        value = None
        while True:
            self.io.output.flush()
            value = root.match(self.io.input.read())
            if value == None:
                self.io.output('Sorry I did not understand that. Try Again')
                self.io.output.flush()
            else:
                return value


    def processFilled(self, element, value):
        text = True
        for child in element:
            if child.tag == 'if':
                text = False
                self.processIf(child, value)        
        if text:
            self.io.output(element.text)

    def processIf(self, element, value):
        cond = element.attrib['cond']
        # No this will not work with other VXML
        status = value == 'true'
        if cond[0] == '!':
            status = not status
        clear =  element.find('clear')
        if status:
            list = clear.attrib['namelist'].split()
            self.retryFields(list)
    
    # I totaly forgot about confirmations hence the patch...
    def retryFields(self, list):
        fields = self.form.findall('field')
        toRetry = [f for f in fields if list.count(f.attrib['name']) > 0]
        for f in toRetry:
            self.processField(f)       


class Rule(object):
    def __init__(self, ruleXML):
        self.tokens = dict()
        # <one-of> elements
        groups = ruleXML.findall('one-of')
        for g in groups:
            # Iterate over <item> elements in current group
            for item in g:
                result = self.getTag(item)
                self.tokens[item.text.strip()] =  result
    def getTag(self, item):
        result = item.find('tag').text.split('=')[1].strip()
        if result[0] == "'":
            # Remove start and end '  And semicolon
            result = result[1:len(result) -2]
        else:
            # Remove semicolon at the end
            result = result[0:len(result) - 1]
        return result

    def match(self, word):
        if word in self.tokens:
            return self.tokens[word]
        else:
            return None





