#! /usr/bin/env python3

logo = '''
                    _        _ _     _         
   /\/\   ___ _ __ | |_ __ _| (_)___| |_       
  /    \ / _ \ '_ \| __/ _` | | / __| __|      
 / /\/\ \  __/ | | | || (_| | | \__ \ |_       
 \/    \/\___|_| |_|\__\__,_|_|_|___/\__|   
'''

import sys
import os

if (sys.version_info < (3, 0)):
    print('Error: Mentalist only works with Python 3')
    sys.exit(1)

from . import version
from . import model
from . import view

import json
import datetime

class Controller():
    '''The Controller drives the application and mediates between model and view
    '''
    
    def __init__(self):
        self.model = model.Chain()
        self.mainview = view.MainWindow(self)
        
        # how many attributes are currently counting words
        self.word_calculator_count = 0
        # whether we're in the middle of exiting the program
        self.exiting = False
    
        self.load_default_chain()

    def main(self):
        '''Open the main window and start the GUI
        '''
        self.mainview.mainloop()
    
    def exit(self):
        '''Exit the program
        '''
        self.exiting = True
        for i in range(len(self.model.nodes)-1, -1, -1):
            self.model.remove_node(i) # Stop counting words in FileAttr
        sys.exit(0)
    
    def add_node(self, type_):
        '''Add a node to the chain with the given type and update the display
        type_: 'base', 'Case', 'Substitution', 'Append', or 'Prepend'
        '''
        widget_kwargs = {"controller": self,
                         "master": self.mainview.scr_box.interior,
                         "main": self.mainview,
                         "number": len(self.mainview.nodes) + 1}
        
        if type_ == 'base':
            widget = view.BaseWordsNode(right_label_text='Calculating...',
                                        allow_remove=False,
                                        **widget_kwargs)
            node = model.BaseNode(is_root=True)
            self.mainview.set_base_file_box(widget)
        elif type_ == 'Case':
            widget = view.CaseNode(**widget_kwargs)
            node = model.MutateNode(is_case=True)
        elif type_ == 'Substitution':
            widget = view.SubstitutionNode(**widget_kwargs)
            node = model.MutateNode()
        elif type_ in ['Append', 'Prepend']:
            widget = view.AdderNode(type_=type_, **widget_kwargs)
            node = model.AddNode(prepend=type_=='Prepend')
        else:
            print("Unexpected type received in add_node: %s" % type_)
            return

        self.model.add_node(node)
        self.mainview.nodes.append(widget)
        self.update_counts()

    def file_attr_error(self, target_attr_model):
        '''A FileAttr has encountered an error opening its file. Display the
        error and add a "Locate file" button on the node.
        '''
        target_attr_view = None
        for node_model, node_view in zip(self.model.nodes, self.mainview.nodes):
            for attr_model, attr_view in zip(node_model.attrs, node_view.attrs):
                if attr_model == target_attr_model:
                    target_attr_view = attr_view
                    target_node_view = node_view
    
        self.mainview.process_mb.configure(state='disabled')
    
        target_node_view.set_file_error(target_attr_view, target_attr_model.file_error)
        
    def update_counts(self):
        '''Update the word and byte count displays in the upper status bar and
        in nodes that have word counts
        '''
        if self.exiting:
            return
            
        # Update the main word count
        if self.word_calculator_count == 0:
            word_count = self.model.count_words()
        else:
            word_count = "Calculating..."
    
        self.mainview.update_total_words(word_count)
        self.mainview.update_est_opt_size(self.model.count_bytes())
        
        has_file_error = False
        chain_calculating = False
        
        # Update the right-justified word counts in nodes and attributes
        for node_model, node_view in zip(self.model.nodes, self.mainview.nodes):
            calculating = False # whether any attr in this node is still calculating
            for attr_model, attr_view in zip(node_model.attrs, node_view.attrs):
                if attr_model.calculating:
                    calculating = True
                    chain_calculating = True
                elif attr_view.right_label is not None:
                    word_count = attr_model.count_words(0)
                    word_count = view.word_count_to_string(word_count)
                    attr_view.right_label.configure(text=word_count)
        
                if isinstance(attr_model, model.FileAttr) and attr_model.file_error is not None:
                    has_file_error = True
            
            if node_view.right_label is not None:
                if calculating:
                    word_count = "Calculating..."
                else:
                    word_count = node_model.count_words(0)
                    word_count = view.word_count_to_string(word_count)
                node_view.right_label.configure(text=word_count)

        # Disable or re-enable the 'Process' button
        if has_file_error or chain_calculating:
            if self.mainview.process_mb['state'] == 'normal':
                self.mainview.process_mb.configure(state='disabled')
        elif self.mainview.process_mb['state'] == 'disabled' and len(self.model.nodes) > 0 and  (len(self.model.nodes[0].attrs) != 0) and not chain_calculating:
            self.mainview.process_mb.configure(state='normal')

    def remove_node(self, node_idx):
        '''Remove a node from the chain and update the display
        node_idx: the integer index of the node to remove in the model and
        view's node lists
        '''
        self.model.remove_node(node_idx)
        self.mainview.remove_node(node_idx)

        self.update_counts()
    
    def move_node(self, index, direction):
        '''Move the node it the given integer index to a different position
        in the chain, given the direction 'up' or 'down'
        '''
        for nodes in self.model.nodes, self.mainview.nodes:
            if direction == 'up' and index == 1:
                return
            if direction == 'down' and index == len(nodes) - 1:
                return
            if direction == 'up':
                sub_list = [nodes[index], nodes[index - 1]] + nodes[index + 1:]
                new_index = index - 1
            else:
                sub_list = [nodes[index + 1], nodes[index]] + nodes[index + 2:]
                new_index = index
            nodes[new_index:] = sub_list
        return sub_list
    
    def add_attr(self, label, node_view, attr_class, right_label_text=None, *args, **kwargs):
        '''Add a new attr to the node with node node_view. The new attr
        model object is created by calling attr_class with args and kwargs.
        
        label: the attribute's display label
        node_view: the view of the node to add to
        attr_class: the class of the attribute to be created
        right_label_text: a string to display on the right hand side of the
            attribute, indicating a word count or 'Calculating...', or None to
            display no label
        '''
        node_idx = self.mainview.nodes.index(node_view)
        attr = attr_class(label=label, *args, **kwargs)
        
        try:
            self.model.nodes[node_idx].add_attr(attr)
        except model.DuplicateAttrException:
            self.mainview.showerror('Duplicate attribute', 'The node already contains this attribute, ignoring: ' + label)
            return
        
        self.mainview.nodes[node_idx].add_attr(label, right_label_text)
        
        # This occurs when de-serializing a chain with missing files
        if isinstance(attr, model.FileAttr) and attr.file_error is not None:
            self.file_attr_error(attr)
        
        self.update_counts()

    def remove_attr(self, node_view, attr_view):
        '''Remove the attribute attr_view from the node node_view
        '''
        node_idx = self.mainview.nodes.index(node_view)
        attr_idx = node_view.attrs.index(attr_view)
        self.model.nodes[node_idx].attrs[attr_idx].stop_calculating()
        
        del self.model.nodes[node_idx].attrs[attr_idx]
        node_view.remove_attr(attr_view)
        
        self.update_counts()
        
    def load_default_chain(self):
        '''Create the default chain: English dict
        '''
        if len(self.mainview.nodes) != 0:
            self.clear_chain()

        self.add_node('base')
        base_node = self.mainview.nodes[-1]

        # Add the English dictionary by default
        label, path = model.FileAttr.named_files[0]
        self.add_attr(label=label, right_label_text='Calculating...',
                      node_view=base_node,
                      attr_class=model.FileAttr, path=path,
                      controller=self)
   
    def clear_chain(self):
        '''Clear the current chain
        '''
        for i in range(len(self.mainview.nodes)-1, -1, -1):
            self.remove_node(i)
        self.word_calculator_count = 0

    def load(self, path):
        '''Load a chain stored on disk
        '''
        try:
            d = json.load(open(path, 'r'))
        except:
            self.mainview.showerror('Invalid JSON in chain file', 'The file {} is not a valid chain file'.format(path))
            return
        
        self.clear_chain()
        
        try:
            model.Serializable.load_string_dict(d, controller=self)
        except:
            self.mainview.showerror('Invalid chain file', 'The file {} is not a valid chain file'.format(path))
            self.load_default_chain()

    def save(self, path):
        '''Save a chain to disk
        '''
        d = model.Serializable.chain_as_string_dict(self.model, version)
        json.dump(d, open(path, 'w'))
    
    def check_hashcat_compatible(self):
        return self.model.check_hashcat_compatible()

    def to_hashcat(self, path, comments):
        '''Output hashcat rules with comment string at the top
        '''
        start_time = datetime.datetime.now()
        
        rules = self.model.get_rules()
        rule_count_string = view.main.word_count_to_string(len(rules.split('\n')) - 1)
        rules = '\n'.join([comments, '#\n# Total Rules: {}'.format(rule_count_string), rules])
        
        open(path, 'w').write(rules)
        
        end_time = datetime.datetime.now()
        print('Running time (seconds):', (end_time - start_time).seconds)
        print('Rule count:', rule_count_string)
        print()
        print('------ OUTPUT COMPLETE ------')
        print()

    def process(self, path, basewords_only):
        '''Output the words to a file
        
        basewords_only: bool, whether to output just the basewords rather than
            processing the whole chain
        '''
        # First handle any missing user files
        has_file_error = False
        for node in self.model.nodes:
            for attr in node.attrs:
                if isinstance(attr, model.FileAttr):
                    attr.check_file()
                    if attr.file_error is not None:
                        self.file_attr_error(attr)
                        has_file_error = True
        if has_file_error:
            return
            
        if basewords_only:
            word_count = self.model.nodes[0].count_words(0)
            word_count_str = view.word_count_to_string(word_count)
            print('Est. Total Words:', word_count_str)
            byte_count = self.model.nodes[0].count_bytes(0, 0)
            byte_count += word_count
            byte_count_str = view.main.get_size_str(byte_count)
            print('Est. Total Size:', byte_count_str)
            print()
        else:
            print('Est. Total Words:', self.mainview.word_count_str)
            print('Est. Total Size:', self.mainview.byte_count_str)
            print()

        # Now pull all the words from the model and write them to the output
        start_time = datetime.datetime.now()
        f = open(path, "w", errors='ignore')
        
        # This counts the words output so far, to know when to update progress
        output_word_count = 0
        output_byte_count = 0
        progress_percent = 0.
        
        try:
            self.mainview.start_progress_bar(path)
            
            # This flag is used to cancel processing from another thread
            self.stop_processing_flag = False
            
            for word in self.model.get_words(basewords_only):
                if self.exiting or self.stop_processing_flag:
                    self.mainview.cancel_progress_bar()
                    os.remove(path)
                    print('Cancelled processing of', path)
                    return
                
                f.write(word + "\n")
                output_word_count += 1
                
                if output_word_count % 5000 == 0: # process cancel button
                    self.mainview.progress_popup.update()
                
                if output_word_count % 100 == 0: # don't check too often
                    new_percent = self.model.get_progress_percent()
                    # update the progress bar when the integer % changes
                    if int(new_percent) != int(progress_percent):
                        self.mainview.update_progress_bar(new_percent)
                        progress_percent = new_percent
        except model.FileException:
            pass
        f.close()
        
        self.mainview.progress_bar_done()
        
        end_time = datetime.datetime.now()
        print('Running time (seconds):', (end_time - start_time).seconds)
        print('Word count:', view.main.word_count_to_string(output_word_count))
        print()
        print('------ OUTPUT COMPLETE ------')
        print()

def main():
    print(logo)
    print('v', version)
    print('by sc0tfree')
    print()
    controller = Controller()
    controller.main()
