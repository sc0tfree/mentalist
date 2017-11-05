#! /usr/bin/env python

import os
import threading
from abc import abstractmethod

import calendar
import datetime
import inspect
import copy
import sys

script_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(script_dir, 'data')

class Serializable(object):
    '''
    Helper class for serializing chains. Only subclasses and allowed_typenames
    are allowed to be serialized, avoiding the security problems of pickle.
    '''
    allowed_typenames = ['NoneType', 'bool', 'int', 'str', 'list']

    def chain_as_string_dict(chain, version):
        '''Gets a representation of the chain as a dictionary of strings
        '''
        chain_dict = {'nodes': [], 'version': version}
        
        for node in chain.nodes:
            node_dict = {'attributes': []}
            
            class_name = node.__class__.__name__
            if class_name == 'BaseNode':
                node_dict['type_'] = 'base'
            elif class_name == 'MutateNode':
                if node.is_case:
                    node_dict['type_'] = 'Case'
                else:
                    node_dict['type_'] = 'Substitution'
            elif class_name == 'AddNode':
                if node.prepend:
                    node_dict['type_'] = 'Prepend'
                else:
                    node_dict['type_'] = 'Append'
            
            for attr in node.attrs:
                attr_dict = {'class_name': attr.__class__.__name__,
                             'kwargs': {}}
                
                # Get all of the members with names matching args to __init__
                for name in inspect.getargspec(attr.__class__.__init__)[0]:
                    if name in ['self', 'controller']:
                        continue

                    val = attr.__dict__[name]
                    val_class_name = val.__class__.__name__
                    if val_class_name not in Serializable.allowed_typenames:
                        raise Exception('Cannot serialize attr of class:',
                                        val_class_name)
                    
                    attr_dict['kwargs'][name] = val
                        
                node_dict['attributes'].append(attr_dict)
                    
            chain_dict['nodes'].append(node_dict)

        return chain_dict
    
    def load_string_dict(d, controller):
        '''Re-creates the chain from a dictionary of strings by calling
        add_node() and add_attr() on the controller
        '''
        # Get the names of all subclasses of Serializable
        def get_subclasses(class_):
            sub = {class_.__name__}
            for subclass in class_.__subclasses__():
                sub.update(get_subclasses(subclass))
            return sub
        allowed_classes = get_subclasses(Serializable)
        
        if len(d['nodes']) == 0 or d['nodes'][0]['type_'] != 'base':
            raise Exception('The chain must start with a BaseNode')
        
        for node_dict in d['nodes']:
            controller.add_node(type_=node_dict['type_'])

            for attr_dict in node_dict['attributes']:
                class_name = attr_dict['class_name']
                if class_name in allowed_classes:
                    attr_class = globals()[class_name]
                    if issubclass(attr_class, ThreadingAttr):
                        attr_dict['kwargs']['controller'] = controller
                controller.add_attr(node_view=controller.mainview.nodes[-1],
                                    attr_class=attr_class,
                                    **attr_dict['kwargs'])

        controller.update_counts()

class Chain(Serializable):
    '''A chain is a sequence of nodes that produces output words
    '''
    def __init__(self):
        self.nodes = []
        self.baseword_count_ = None

    def add_node(self, node):
        self.nodes.append(node)
        self.baseword_count_ = None
    
    def remove_node(self, idx):
        for attr in self.nodes[idx].attrs:
            attr.stop_calculating() # Stop counting words in FileAttr
        del self.nodes[idx]
        self.baseword_count_ = None
    
    def get_words(self, basewords_only=False):
        '''A generator that yields the chain's words
        '''
        for attr in self.nodes[0].attrs:
            attr.words_read = 0
        
        if basewords_only:
            for word in self.nodes[0].get_words([]):
                yield word
        else:
            words = []
            for node in self.nodes:
                words = node.get_words(words)
            for word in words:
                yield word

    def count_words(self):
        '''Returns the total number of words produced by this chain
        '''
        count = 0
        for node in self.nodes:
            count = node.count_words(count)
        return count

    def count_bytes(self):
        '''Returns the estimated size in bytes of the password file output
        '''
        word_count = 0
        byte_count = 0
        for node in self.nodes:
            byte_count = node.count_bytes(byte_count, word_count)
            word_count = node.count_words(word_count)
        if byte_count > 0:
            byte_count += word_count # count the newline characters
        return byte_count

    def check_hashcat_compatible(self):
        '''Returns True if all nodes and their attributes can be turned into
        hashcat rules
        '''
        result = True
        for node in self.nodes:
            result = result and node.check_hashcat_compatible()
        return result

    def get_rules(self):
        '''Generates a hashcat rulefile representing the chain
        
        return value: the rulefile string
        '''
        # build up lines of the rule file
        # each line is a list of strings
        lines = [[]]
        for node in self.nodes:
            lines = node.get_rules(lines)
        return '\n'.join([''.join(line) for line in lines]) + '\n'

    def get_progress_percent(self):
        '''While get_words is generating output words, this returns an estimate
        (integer percent) of how close to completion it is.
        '''
        if self.baseword_count_ is None:
            self.baseword_count_ = 0
            for attr in self.nodes[0].attrs:
                if attr.calculating:
                    self.baseword_count_ = None
                    break
                else:
                    self.baseword_count_ += attr.count_words(0)
    
        if self.baseword_count_ is None:
            return 0
        else:
            progress_count = 0
            for attr in self.nodes[0].attrs:
                progress_count += attr.words_read
            return int(100. * progress_count / self.baseword_count_)

class DuplicateAttrException(Exception):
    '''Raised in a node's add_attr to indicate that an identical attribute is
    already present
    '''
    pass

class BaseNode(Serializable):
    '''A node produces output words, and may take input words which it may
    modify and then output them.
    '''

    def __init__(self, is_root=True):
        '''is_root: bool, whether this is the first attr in the chain
        '''
        self.is_root = is_root
        self.attrs = []

    def add_attr(self, attr):
        '''Add an attribute to the node. May raise DuplicateAttrException.
        '''
        if attr in self.attrs:
            raise DuplicateAttrException()
        else:
            self.attrs.append(attr)

    def get_words(self, prev_words):
        '''A generator that yields the node's words, given the sequence of
        input words prev_words
        '''
        if self.is_root:
            assert len(list(prev_words)) == 0 # there cannot be any previous words
        
        for attr in self.attrs:
            for word in attr.get_words(prev_words):
                yield word

    def count_words(self, prev_word_count):
        '''Estimates the number of words generated by this node
        '''
        if self.is_root:
            assert prev_word_count == 0

        if len(self.attrs) == 0:
            return prev_word_count
        else:
            count = 0
            for attr in self.attrs:
                count += attr.count_words(prev_word_count)
            return count

    def count_bytes(self, prev_byte_count, prev_word_count):
        '''Estimates the number of bytes in the words generated by this node
        '''
        if self.is_root:
            assert prev_byte_count == 0
        
        byte_count = prev_byte_count
        for attr in self.attrs:
            byte_count += attr.count_bytes(prev_byte_count, prev_word_count)
        return byte_count

    def check_hashcat_compatible(self):
        result = True
        for attr in self.attrs:
            result = result and attr.check_hashcat_compatible()
        return result

    def get_rules(self, lines):
        return [[]]

class MutateNode(BaseNode):
    '''Changes the characters in the word, including changing the case of
    letters and substituting one character for another
    '''
    def __init__(self, is_case=False):
        self.is_case = is_case
        BaseNode.__init__(self, is_root=False)

    def get_words(self, prev_words):
        if len(self.attrs) == 0:
            for word in prev_words:
                yield word
        else:
            dedupe = True
            if dedupe and len(self.attrs) > 1:
                for prev_word in prev_words:
                    new_words = set()
                    for attr in self.attrs:
                        for word in attr.get_words([prev_word]):
                            new_words.update([word])
                    for word in new_words:
                        yield word
            else:
                for prev_word in prev_words:
                    for attr in self.attrs:
                        for word in attr.get_words([prev_word]):
                            yield word

    def count_words(self, prev_word_count):
        if len(self.attrs) == 0:
            return prev_word_count
    
        if self.is_case:
            return BaseNode.count_words(self, prev_word_count)
        else:
            # Use heuristics to estimate Substitution word count
            count = 0
            
            for attr in self.attrs:
                if isinstance(attr, NothingMutatorAttr):
                    count = 1 * prev_word_count
                    break
            
            for attr in self.attrs:
                if isinstance(attr, SubstitutionAttr):
                    for f in attr.character_freqs:
                        if count == 0:
                            count = 1 * prev_word_count
                        else:
                            count += int(f * prev_word_count)

            return count

    def count_bytes(self, prev_byte_count, prev_word_count):
        if len(self.attrs) == 0:
            return prev_byte_count

        if self.is_case:
            byte_count = 0
            for attr in self.attrs:
                byte_count += attr.count_bytes(prev_byte_count, prev_word_count)
        else:
            byte_count = 0
            
            for attr in self.attrs:
                if isinstance(attr, NothingMutatorAttr):
                    byte_count = 1 * prev_byte_count
                    break
            
            for attr in self.attrs:
                if isinstance(attr, SubstitutionAttr):
                    for f in attr.character_freqs:
                        if byte_count == 0:
                            byte_count = prev_byte_count
                        else:
                            byte_count += int(f * prev_byte_count)

        return byte_count

    def get_rules(self, lines):
        new_lines = []
        
        if len(self.attrs) == 0:
            for line in lines:
                new_lines.append(line + [':'])
        
        for attr in self.attrs:
            attr_lines = attr.get_rules()
            for attr_line in attr_lines:
                for line in lines:
                    new_line = copy.copy(line)
                    new_line.append(attr_line)
                    new_lines.append(new_line)
    
        return new_lines

class AddNode(BaseNode):
    '''Append or prepend a string to the word
    '''
    def __init__(self, prepend=False):
        BaseNode.__init__(self, is_root=False)
        self.prepend = prepend

    def get_words(self, prev_words):
        if len(self.attrs) == 0:
            for word in prev_words:
                yield word
    
        for word in prev_words:
            for attr in self.attrs:
                for other_word in attr.get_words([]):
                    if self.prepend:
                        yield other_word + word
                    else:
                        yield word + other_word

    def count_words(self, prev_word_count):
        if len(self.attrs) == 0:
            return prev_word_count
        
        multiplier = 0
        for attr in self.attrs:
            multiplier += attr.count_words(0)
        return multiplier * prev_word_count

    def count_bytes(self, prev_byte_count, prev_word_count):
        if len(self.attrs) == 0:
            return prev_byte_count
    
        attr_word_count = 0
        attr_byte_count = 0
        for attr in self.attrs:
            attr_word_count += attr.count_words(0)
            attr_byte_count += attr.count_bytes(0, 0)
        
        byte_count = BaseNode.count_bytes(self, prev_byte_count, prev_word_count)
        return attr_word_count * prev_byte_count + prev_word_count * attr_byte_count

    def get_rules(self, lines):
        new_lines = []
        
        if len(self.attrs) == 0:
            for line in lines:
                new_lines.append(line + [':'])
        
        for attr in self.attrs:
            if isinstance(attr, NothingAdderAttr):
                for line in lines:
                    new_lines.append(line + [':'])
            else:
                for word in attr.get_words([]):
                    for line in lines:
                        new_line = copy.copy(line)
                        if self.prepend:
                            command = '^'
                        else:
                            command = '$'
                        new_line.extend([command + c for c in word])
                        new_lines.append(new_line)
    
        return new_lines

class BaseAttr(Serializable):
    '''An attribute defines the behavior of the node. Typically each attribute
    produces one or more words.
    '''
    def __init__(self, label=""):
        self.label = label
        self.calculating = False

    @abstractmethod
    def get_words(self, prev_words):
        pass
    
    @abstractmethod
    def count_words(self, prev_word_count):
        pass

    @abstractmethod
    def count_bytes(self, prev_byte_count, prev_word_count):
        pass
    
    def check_hashcat_compatible(self):
        return True
    
    def __eq__(self, other):
        '''This is used to avoid duplicate attributes within a node
        '''
        if self.__class__ != other.__class__:
            return False
    
        # This checks whether the two attributes have the same values for their
        # __init__ arguments (like in serialization)
        result = True
        for name in inspect.getargspec(self.__class__.__init__)[0]:
            if name in ['self', 'controller']:
                continue
            if (name in other.__dict__) and (self.__dict__[name] != other.__dict__[name]):
                result = False
        return result
    
    def __ne__(self, other):
        return not self == other

    def stop_calculating(self):
        '''Stop calculating word counts (only needed for FileAttr)
        '''
        pass

class StringListAttr(BaseAttr):
    def __init__(self, strings, label=""):
        BaseAttr.__init__(self, label)
        self.strings = strings
        self.byte_count = sum(map(len, self.strings))
    
        self.words_read = None # used for the progress indicator

    def get_words(self, prev_words=[]):
        self.words_read = 0
        for word in prev_words:
            yield word
        for s in self.strings:
            self.words_read += 1
            yield s

    def count_words(self, prev_word_count):
        return prev_word_count + len(self.strings)
    
    def count_bytes(self, prev_byte_count, prev_word_count):
        return self.byte_count

class ThreadingAttr(BaseAttr):
    '''This indicates that the derived class calculates its word count in
    a background thread, takes a controller instance and communicates with it
    when it is done calculating
    '''

    def stop_calculating(self):
        self.kill_flag = True
        self.worker_thread.join()
    '''
    def __del__(self):
        # note that __del__ is not always called immediately with 'del'
        self.stop_calculating()
    '''

class FileException(Exception):
    '''This is raised when any sort of exception occurs with FileAttr's file
    '''
    pass

class FileAttr(ThreadingAttr):
    '''Generates one word for each line in a file
    '''
    
    # named_files is read by the GUI to generate the file menus
    named_files = [['English Dictionary', '$DATA_DIR/English_Dict.txt'],
                   ['Common Names', [['Men', '$DATA_DIR/Common_Names_Men.txt'],
                                     ['Women', '$DATA_DIR/Common_Names_Women.txt'],
                                     ['Pets', '$DATA_DIR/Common_Names_Pets.txt']]],
                   ['Other', [['Slang & Expletives', '$DATA_DIR/Slang_And_Expletives.txt'],
                              ['Months & Seasons', '$DATA_DIR/Months_And_Seasons.txt']]]
                  ]
    
    def __init__(self, path, controller=None, label=""):
        BaseAttr.__init__(self, label)
        self.path = path
        self.controller = controller
        
        self.absolute_path = path.replace('$DATA_DIR', data_dir)
        
        self.file_error = None
        
        try:
            self.byte_count = os.stat(self.absolute_path).st_size
            
            # Windows seems to always report an extra two bytes
            if sys.platform == 'win32':
                self.byte_count -= 2
    
        except Exception as e:
            self.file_error = str(e)
            self.word_count = 0
            self.byte_count = 0
         
        # This is used by the progress bar to keep track of how many lines
        # have been read in get_words(). It is reset when the file is done.
        self.words_read = None
        
        self.word_count = 1
    
        self.calculating = True
        if self.controller is not None:
            self.controller.word_calculator_count += 1
            self.controller.update_counts() # update word counts to 'Calculating...'
            self.worker_thread = threading.Thread(target=self.threaded_word_counter)
            self.kill_flag = False
        else:
            # When there is no controller (in model tests), run the word counter
            # in the main thread
            self.kill_flag = False
            self.threaded_word_counter()
        
        if self.controller is not None:
            self.worker_thread.start()
            
    def check_file(self):
        '''Check whether the file is present
        '''
        try:
            os.stat(self.absolute_path)
        except Exception as e:
            self.file_error = str(e)

    def threaded_word_counter(self):
        '''In order to estimate the number of words, this method is run in a
        background thread and reads the number of lines in the input file.
        '''
        if self.file_error is not None:
            self.controller.word_calculator_count -= 1
            return
    
        try:
            i = 0
            try:
                with open(self.absolute_path, errors='ignore') as f:
                    for i, line in enumerate(f):
                        if self.kill_flag:
                            break
            except Exception as e:
                self.file_error = str(e)
                self.controller.file_attr_error(self)
                return
            i += 1
            self.word_count = i
            self.byte_count -= self.word_count - 1 # don't count newlines
            self.calculating = False
            if self.controller is not None:
                self.controller.word_calculator_count -= 1
                self.controller.update_counts()
        except Exception as e:
            print("Exception while counting words:", e)

    def get_words(self, prev_words=[]):
        self.words_read = 0
            
        for word in prev_words:
            yield word
    
        try:
            for line in open(self.absolute_path, errors='surrogateescape'):
                if line[-1] == '\n':
                    line = line[:-1]
                self.words_read += 1
                yield line

        except Exception as e:
            self.file_error = str(e)
            if self.controller:
                self.controller.file_attr_error(self)
                raise FileException()
            else:
                raise
    
    def count_words(self, prev_word_count):
        return prev_word_count + self.word_count
        
    def count_bytes(self, prev_byte_count, prev_word_count):
        return prev_byte_count + self.byte_count

class RangeAttr(BaseAttr):
    '''Generates each number in an integer range
    '''
    def __init__(self, start, end, zfill=0, label=""):
        '''
        start, end: integers as in Python's range()
        zfill: pad with leading zeros to this length
        '''
        BaseAttr.__init__(self, label)
        self.start = start
        self.end = end
        self.zfill = zfill
    
        self.byte_count = 0
        for i in range(self.start, self.end):
            self.byte_count += len(str(i).zfill(zfill))
    
    def get_words(self, prev_words):
        for word in prev_words:
            yield word

        for i in range(self.start, self.end):
            yield str(i).zfill(self.zfill)

    def count_words(self, prev_word_count):
        return prev_word_count + (self.end - self.start)
        
    def count_bytes(self, prev_byte_count, prev_word_count):
        return self.byte_count

class DateRangeAttr(ThreadingAttr):
    '''Generates numerical date strings for a range of dates with the given format
    '''
    def __init__(self, start_year, end_year, format, zero_padding, controller=None, label=""):
        '''
        controller: used to communicate about word counting
        start_year, end_year: integers as in Python's range()
        format: a string indicating the date format, for example mmddyyyy
        zero_padding: a boolean indicating whether single-digit months and days
                      should have leading zeros
        '''
        BaseAttr.__init__(self, label)
        self.start_year = start_year
        self.end_year = end_year
        self.format = format
        self.zero_padding = zero_padding
        self.controller = controller
        
        self.calculating = True
        if self.controller is not None:
            self.controller.word_calculator_count += 1
            self.controller.update_counts() # update word counts to 'Calculating...'
            self.worker_thread = threading.Thread(target=self.threaded_word_counter)
            self.kill_flag = False
        else:
            # When there is no controller (in model tests), run the word counter
            # in the main thread
            self.kill_flag = False
            self.threaded_word_counter()
        
        if self.controller is not None:
            self.worker_thread.start()
    
    def threaded_word_counter(self):
        '''The date strings are pre-computed, but take a few seconds to compute,
        so do it in a background thread
        '''
        # convert the format to a Python format string
        four_digit_year = 'yyyy' in self.format
        has_year = 'y' in self.format
        has_day = 'd' in self.format
        
        type_list = [self.format[0]]
        if has_year and has_day:
            type_list.append([f for f in ['m', 'd', 'y'] \
                              if f not in [self.format[0], self.format[-1]]][0])
        type_list.append(self.format[-1])
        
        format_items = []
        for t in type_list:
            format_items.extend(['{', t])
            if (t in ['m', 'd'] and self.zero_padding) or (t == 'y'):
                format_items.append(':02')
            format_items.append('}')

        format_string = ''.join(format_items)
        
        self.dates = []
        self.byte_count = 0
        for year in range(self.start_year, self.end_year):
            if self.kill_flag:
                break
            
            if four_digit_year:
                display_year = year
            else:
                display_year = year - (year // 100) * 100
            for month in range(1, 13):
                if has_day:
                    weekdays, days = calendar.monthrange(year, month)
                    for day in range(1, days+1):
                        if self.kill_flag:
                            break
                        
                        if has_year:
                            date = format_string.format(y=display_year, m=month, d=day)
                        else:
                            date = format_string.format(m=month, d=day)
                        if date not in self.dates:
                            self.dates.append(date)
                            self.byte_count += len(date)
                else:
                    date = format_string.format(y=display_year, m=month)
                    self.dates.append(date)
                    self.byte_count += len(date)

        self.calculating = False
        if self.controller is not None:
            self.controller.word_calculator_count -= 1
            if not self.kill_flag:
                self.controller.update_counts()
        
    def get_words(self, prev_words):
        for word in prev_words:
            yield word

        for date in self.dates:
            yield date

    def count_words(self, prev_word_count):
        return prev_word_count + len(self.dates)
        
    def count_bytes(self, prev_byte_count, prev_word_count):
        return self.byte_count


def load_codes(location_type, code_type):
    '''Load zip codes and area codes
    '''
    path = os.path.join(data_dir, '-'.join([location_type, code_type])+'.psv')
    code_dict = {}
    i = 0
    for line in open(path).read().split('\n'):
        if line == '': continue # allow final newline
        location, codes = line.split('|')
        i += 1
        codes = codes.split(',')
        if location in code_dict:
            code_dict[location].extend(codes)
        else:
            code_dict[location] = codes
    return code_dict

location_codes = {}
for location_type in ['City', 'State']:
    location_codes[location_type] = {}
    for code_type in ['Area', 'Zip']:
        location_codes[location_type][code_type] = load_codes(location_type, code_type)

def clean_code_file(location_type, code_type):
    '''Utility for outputting sorted version of code file with no duplicates
    '''
    path = os.path.join(data_dir, '-'.join([location_type, code_type])+'.psv')
    f = open(path, 'w')
    for state, codes in sorted(location_codes[location_type][code_type].items()):
        f.write('|'.join([state, ','.join(sorted(set(codes)))])+'\n')

class LocationCodeAttr(BaseAttr):
    '''Generates zip codes and area codes
    '''
    def __init__(self, code_type, location, location_type, label=""):
        '''
        code_type: 'Area' or 'Zip'
        location_type: 'City' or 'State'
        location: string, like 'Boston, MA' or 'CA'
        '''
        BaseAttr.__init__(self, label)
        self.code_type = code_type
        self.location = location
        self.location_type = location_type
        
        codes_dict = location_codes[location_type][code_type]
        self.codes = codes_dict[self.location]
        self.byte_count = sum(map(len, self.codes))

    def get_words(self, prev_words):
        for word in prev_words:
            yield word

        for code in self.codes:
            yield code

    def count_words(self, prev_word_count):
        return prev_word_count + len(self.codes)
        
    def count_bytes(self, prev_byte_count, prev_word_count):
        return self.byte_count

class NothingMutatorAttr(BaseAttr):
    '''Generates just the unmodified input words, with no mutation
    '''
    def get_words(self, prev_words):
        return prev_words

    def count_words(self, prev_word_count):
        return prev_word_count
        
    def count_bytes(self, prev_byte_count, prev_word_count):
        return prev_byte_count
    
    def get_rules(self):
        return [':']

class NothingAdderAttr(BaseAttr):
    '''Generates just the unmodified input words, with nothing appended
    '''
    def get_words(self, prev_words):
        return [""]

    def count_words(self, prev_word_count):
        return prev_word_count + 1
        
    def count_bytes(self, prev_byte_count, prev_word_count):
        return prev_byte_count

class CaseAttr(BaseAttr):
    '''Modifies the case of letters in the word
    '''
    def __init__(self, type_, case=None, idx=None, label=""):
        '''
        type_: 'First' (just the first letter), 'All' (all letters), or 'Toggle'
               (switch upper case to lower case, and vice versa)
        case: 'Uppercase', 'Lowercase' (change letters to this case), or None
              (for Toggle)
        idx: Modify the character at this index
        '''
        BaseAttr.__init__(self, label=label)
        self.type_ = type_
        self.case = case
        self.idx = idx

    def get_words(self, prev_words):
        for word in prev_words:
            if word == "":
                yield word
                continue
        
            if self.type_ == 'First':
                string_list = list(word)
                if self.case == 'Lowercase':
                    string_list[0] = string_list[0].lower()
                    for i in range(1, len(string_list)):
                        string_list[i] = string_list[i].upper()
                else:
                    string_list[0] = string_list[0].upper()
                    for i in range(1, len(string_list)):
                        string_list[i] = string_list[i].lower()
                yield ''.join(string_list)
            
            elif self.type_ == 'All':
                if self.case == 'Lowercase':
                    yield word.lower()
                else:
                    yield word.upper()
            
            elif self.type_ == 'Toggle':
                if len(word) > self.idx:
                    string_list = list(word)
                    if string_list[self.idx].isupper():
                        string_list[self.idx] = string_list[self.idx].lower()
                    else:
                        string_list[self.idx] = string_list[self.idx].upper()
                    yield ''.join(string_list)
                else:
                    yield word

    def count_words(self, prev_word_count):
        return prev_word_count

    def count_bytes(self, prev_byte_count, prev_word_count):
        return prev_byte_count
    
    def get_rules(self):
        if self.type_ in ['First', 'All']:
            rule = {'First': {'Uppercase': 'c',
                              'Lowercase': 'C'},
                    'All': {'Uppercase': 'u',
                                 'Lowercase': 'l'},
                   }[self.type_][self.case]
        elif self.type_ == 'Toggle':
            rule = 'T{}'.format(self.idx)

        return [rule]

# This file contains the percent of English dictionary words containing at least
# one instance of each letter.
character_freq = {}
for line in open(os.path.join(data_dir, 'Letter_Stats.txt')).read().split('\n'):
    letter, percent = line.split(',')
    character_freq[letter] = float(percent[:-1]) / 100.

class SubstitutionAttr(BaseAttr):
    '''Substitutes one character for another
    '''
    def __init__(self, type_, checked_vals, all_together, label=""):
        '''
        type_: 'First' (substitute the first instance), 'All' (substitute all
               instances), or 'Nth' (substitute the Nth instance)
               
        checked_vals: a list of substitution strings of the form 'old -> new'
        
        all_together: If True, the substitutions in checked_vals will generate
                      one output word for each substitution matching the
                      input word, with the substitutions applied one at a time.
                      If False, just one output word will be generated for each
                      input word, with all substitutions applied together.
        '''
        BaseAttr.__init__(self, label=label)
        self.type_ = type_
        self.checked_vals = checked_vals
        self.all_together = all_together
        
        self.replacements = []
        for check in checked_vals:
            self.replacements.append(check.split(' -> '))
    
        if self.all_together:
            self.character_freqs = [0.]
        else:
            self.character_freqs = []
        for original, _ in self.replacements:
            freq = character_freq.get(original, 0.)
            if all_together:
                self.character_freqs[0] += (1. - self.character_freqs[0]) * freq
            else:
                self.character_freqs.append(freq)

    def get_words(self, prev_words):
        for word in prev_words:
            if word == "":
                yield word
                continue
            
            string_list = list(word)
            if self.type_ in ["First", "All", "Nth"]:
                idx_range = range(len(string_list))
            else:
                idx_range = range(len(string_list) - 1, -1, -1)
            
            found_replacement_word = False
            for original, replacement in self.replacements:
                found_replacement_sub = False

                for i in idx_range:
                    if string_list[i].lower() == original:
                        string_list[i] = replacement
                        found_replacement_word = True
                        found_replacement_sub = True
                        
                        if self.type_ in ['First', 'Last']:
                            if not self.all_together:
                                yield ''.join(string_list)
                                string_list = list(word)
                            break
                    
                if self.type_ == 'All' and found_replacement_sub and not self.all_together:
                    yield ''.join(string_list)
                    string_list = list(word)

            if self.all_together:
                yield ''.join(string_list)
            elif not found_replacement_word:
                yield word

    def check_hashcat_compatible(self):
        if self.type_ in ['First', 'Last']:
            return False
        else:
            return True

    def get_rules(self):
        rules = []
        for original, replacement in self.replacements:
            if len(original) > 1 or len(replacement) > 1:
                print('Warning: excluding multi-character substitution, not supported in hashcat rules:', original, replacement)
            else:
                rules.append('s' + original + replacement)

        if self.all_together:
            return [''.join(rules)]
        else:
            return rules
