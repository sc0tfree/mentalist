import unittest
import warnings
import tempfile
import shutil
import os
import sys
import subprocess

sys.path.insert(1, os.path.join(sys.path[0], '..'))
from mentalist import model

run_hashcat_tests = False

class TestModel(unittest.TestCase):
    def test_file_attr(self):
        attr = model.FileAttr(path=self.test_words_path)
        
        result = list(attr.get_words())
        self.assertEqual(self.test_words, result)
        self.assertEqual(len(result), attr.count_words(0))
    
    def test_stringlist_attr(self):
        attr = model.StringListAttr(strings=self.test_words)
        
        result = list(attr.get_words())
        self.assertEqual(self.test_words, result)
        self.assertEqual(len(result), attr.count_words(0))
    
    def test_case_mutator_attr(self):
        attr = model.CaseAttr(type_='First', case='Uppercase')
        result = list(attr.get_words(['test1', 'test2']))
        self.assertEqual(result, ['Test1', 'Test2'])
        self.assertEqual(len(result), attr.count_words(2))
        
        attr = model.CaseAttr(type_='All', case='Uppercase')
        result = list(attr.get_words(['test1', 'test2']))
        self.assertEqual(result, ['TEST1', 'TEST2'])
        self.assertEqual(len(result), attr.count_words(2))
        
        attr = model.CaseAttr(type_='First', case='Lowercase')
        result = list(attr.get_words(['TEST1', 'TEST2']))
        self.assertEqual(result, ['tEST1', 'tEST2'])
        self.assertEqual(len(result), attr.count_words(2))
        
        attr = model.CaseAttr(type_='Toggle', idx=3)
        result = list(attr.get_words(['test1', 'test2']))
        self.assertEqual(result, ['tesT1', 'tesT2'])
        self.assertEqual(len(result), attr.count_words(2))
        
        attr = model.CaseAttr(type_='Toggle', idx=3)
        result = list(attr.get_words(['', 'test2']))
        self.assertEqual(result, ['', 'tesT2'])
        self.assertEqual(len(result), attr.count_words(2))
    
    def test_substitution_mutator_attr(self):
        attr = model.SubstitutionAttr(type_='All', checked_vals=['e -> 3', 'l -> 1', 'o -> 0'], all_together=True)
        result = list(attr.get_words(['hello', 'test2']))
        self.assertEqual(result, ['h3110', 't3st2'])
        
        attr = model.SubstitutionAttr(type_='All', checked_vals=['e -> 3', 'l -> 1', 'o -> 0'], all_together=False)
        result = list(attr.get_words(['hello', 'test2']))
        self.assertEqual(result, ['h3llo', 'he11o', 'hell0',
                                  't3st2'])
        
        attr = model.SubstitutionAttr(type_='All', checked_vals=['e -> 3', 'l -> 1', 'o -> 0'], all_together=False)
        result = list(attr.get_words(['HELLO', 'test2']))
        self.assertEqual(result, ['H3LLO', 'HE11O', 'HELL0',
                                  't3st2'])
        
        attr = model.SubstitutionAttr(type_='Last', checked_vals=['e -> 3', 'l -> 1', 'o -> 0'], all_together=False)
        result = list(attr.get_words(['HELLO', 'test2']))
        self.assertEqual(result, ['H3LLO', 'HEL1O', 'HELL0', 't3st2'])
        
        attr = model.SubstitutionAttr(type_='First', checked_vals=['e -> 3', 'l -> 1', 'o -> 0'], all_together=True)
        result = list(attr.get_words(['hello', 'test2']))
        self.assertEqual(result, ['h31l0', 't3st2'])
        
        attr = model.SubstitutionAttr(type_='Last', checked_vals=['e -> 3', 'l -> 1', 'o -> 0'], all_together=True)
        result = list(attr.get_words(['hello', 'test2']))
        self.assertEqual(result, ['h3l10', 't3st2'])
    
    def test_range_attr(self):
        range_ = [0, 100]
        attr = model.RangeAttr(start=range_[0], end=range_[1])
        result = list(attr.get_words([]))
        truth = list(map(str, range(*range_)))
        self.assertEqual(result, truth)
        self.assertEqual(len(result), attr.count_words(0))
        
        range_ = [0, 100]
        zfill = 3
        attr = model.RangeAttr(start=range_[0], end=range_[1], zfill=zfill)
        result = list(attr.get_words([]))
        truth = [str(i).zfill(zfill) for i in range(*range_)]
        self.assertEqual(result, truth)
        self.assertEqual(len(result), attr.count_words(0))
    
    def test_daterange_attr(self):
        attr = model.DateRangeAttr(start_year=1950, end_year=1951, format='mmddyyyy', zero_padding=True)
        result = list(attr.get_words([]))
        self.assertEqual(result[-3:], ['12291950', '12301950', '12311950']) # check the last 3 results
        self.assertEqual(result[58:60], ['02281950', '03011950']) # check the leap year
        self.assertEqual(len(result), attr.count_words(0))
        
        attr = model.DateRangeAttr(start_year=1950, end_year=1951, format='yymmdd', zero_padding=True)
        result = list(attr.get_words([]))
        self.assertEqual(result[-3:], ['501229', '501230', '501231']) # check the last 3 results
        self.assertEqual(result[58:60], ['500228', '500301']) # check the leap year
        self.assertEqual(len(result), attr.count_words(0))
        
        attr = model.DateRangeAttr(start_year=1950, end_year=1951, format='mmddyyyy', zero_padding=False)
        result = list(attr.get_words([]))
        self.assertEqual(result[-3:], ['12291950', '12301950', '12311950']) # check the last 3 results
        self.assertEqual(result[58:60], ['2281950', '311950']) # check the leap year
        self.assertEqual(len(result), attr.count_words(0))
        
        attr = model.DateRangeAttr(start_year=1950, end_year=1952, format='mmyy', zero_padding=True)
        result = list(attr.get_words([]))
        self.assertEqual(result[-3:], ['1051', '1151', '1251']) # check the last 3 results
        self.assertEqual(len(result), attr.count_words(0))
        
        attr = model.DateRangeAttr(start_year=1950, end_year=1952, format='mmdd', zero_padding=False)
        result = list(attr.get_words([]))
        self.assertEqual(result[-3:], ['1229', '1230', '1231']) # check the last 3 results
        self.assertEqual(result[58:60], ['228', '31']) # check the leap year
        self.assertEqual(len(result), attr.count_words(0))
    
    def test_locationcode_attr(self):
        attr = model.LocationCodeAttr(code_type='Zip', location='DC', location_type='State')
        result = list(attr.get_words([]))
        self.assertEqual(result[:2], ['20001', '20002'])
        self.assertEqual(len(result), attr.count_words(0))
        
        attr = model.LocationCodeAttr(code_type='Zip', location='Washington, DC', location_type='City')
        result = list(attr.get_words([]))
        self.assertEqual(sorted(result)[:2], ['20001', '20002'])
        self.assertEqual(len(result), attr.count_words(0))
        
        attr = model.LocationCodeAttr(code_type='Area', location='DC', location_type='State')
        result = list(attr.get_words([]))
        self.assertEqual(result[0], '202')
        self.assertEqual(len(result), attr.count_words(0))
        
        attr = model.LocationCodeAttr(code_type='Area', location='Washington, DC', location_type='City')
        result = list(attr.get_words([]))
        self.assertEqual(result[0], '202')
        self.assertEqual(len(result), attr.count_words(0))
    
    def test_adder_node(self):
        attr = model.FileAttr(path=self.test_words_path)
        node = model.AddNode(prepend=True)
        node.add_attr(attr)
        result = list(node.get_words(['A', 'B']))
        self.assertEqual(result, ['test1A', 'test word 2A', 'THIRDTESTWORDA',
                                  'test1B', 'test word 2B', 'THIRDTESTWORDB'])
        self.assertEqual(len(result), node.count_words(2))
        
        attr = model.FileAttr(path=self.test_words_path)
        node = model.AddNode(prepend=False)
        node.add_attr(attr)
        result = list(node.get_words(['A', 'B']))
        self.assertEqual(result, ['Atest1', 'Atest word 2', 'ATHIRDTESTWORD',
                                  'Btest1', 'Btest word 2', 'BTHIRDTESTWORD'])
        self.assertEqual(len(result), node.count_words(2))
                                  
        attr = model.FileAttr(path=self.test_words_path)
        node = model.AddNode(prepend=True)
        node.add_attr(attr)
        attr = model.NothingAdderAttr()
        node.add_attr(attr)
        result = list(node.get_words(['A', 'B']))
        self.assertEqual(result, ['test1A', 'test word 2A', 'THIRDTESTWORDA', 'A',
                                  'test1B', 'test word 2B', 'THIRDTESTWORDB', 'B'])
        self.assertEqual(len(result), node.count_words(2))
                                  
        node = model.AddNode(prepend=True)
        result = list(node.get_words(['A', 'B']))
        self.assertEqual(result, ['A', 'B'])
        self.assertEqual(len(result), node.count_words(2))

    def test_chain(self):
        chain = model.Chain()
        node = model.BaseNode(is_root=True)
        attr = model.FileAttr(path=self.test_words_path)
    
        node.add_attr(attr)
        chain.add_node(node)
        
        result = list(chain.get_words())
        self.assertEqual(self.test_words, result)
        self.assertEqual(len(result), chain.count_words())
        self.assertEqual(len('\n'.join(result)+'\n'), chain.count_bytes())
        self.assertTrue(chain.check_hashcat_compatible())

    def test_serial_mutator_chain(self):
        chain = model.Chain()
        
        node = model.BaseNode(is_root=True)
        attr = model.FileAttr(path=self.test_words_path)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode(is_case=True)
        attr = model.CaseAttr(type_='First', case='Uppercase')
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode(is_case=True)
        attr = model.CaseAttr(type_='Toggle', idx=3)
        node.add_attr(attr)
        chain.add_node(node)
        
        truth_words = ['TesT1', 'TesT word 2', 'ThiRdtestword']
        result = list(chain.get_words())
        self.assertEqual(truth_words, result)
        self.assertEqual(len(result), chain.count_words())
        self.assertEqual(len('\n'.join(result)+'\n'), chain.count_bytes())
        self.assertTrue(chain.check_hashcat_compatible())
    
    def test_long_hashcat_chain(self):
        chain = model.Chain()
        
        strings = ['heLlo', 'worLd']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=strings)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode(is_case=True)
        node.add_attr(model.CaseAttr(type_='First', case='Uppercase'))
        node.add_attr(model.CaseAttr(type_='All', case='Lowercase'))
        node.add_attr(model.NothingMutatorAttr())
        chain.add_node(node)
        
        node = model.MutateNode()
        attr = model.SubstitutionAttr(type_='All', checked_vals=['l -> i', 'l -> 1', 'd -> b'], all_together=False)
        #node.add_attr(model.NothingMutatorAttr()) # differs from hashcat when this is missing
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.AddNode()
        node.add_attr(model.RangeAttr(0, 3))
        chain.add_node(node)
        
        truth_words = [#'Hello', 'heLlo', 'hello', 'World', 'worLd', 'world',
                       'Heiio0', 'heiio0', 'Heiio1', 'heiio1', 'Heiio2', 'heiio2',
                       'He11o0', 'he11o0', 'He11o1', 'he11o1', 'He11o2', 'he11o2',
                       'Worid0', 'worid0', 'Worid1', 'worid1', 'Worid2', 'worid2',
                       'Wor1d0', 'wor1d0', 'Wor1d1', 'wor1d1', 'Wor1d2', 'wor1d2',
                       'Worlb0', 'worLb0', 'Worlb1', 'worLb1', 'Worlb2', 'worLb2',
                       'worlb0', 'worlb1', 'worlb2']
        result = list(chain.get_words())
        self.assertEqual(sorted(truth_words), sorted(set(result)))
        #self.assertEqual(9, chain.count_words())
        #self.assertEqual(len('\n'.join(result)+'\n'), chain.count_bytes())
    
        rules = chain.get_rules()
        self.assert_hashcat_result(truth_words, rules, basewords=strings)
        self.assertTrue(chain.check_hashcat_compatible())
    
        rules_truth = '''csli$0
lsli$0
:sli$0
csl1$0
lsl1$0
:sl1$0
csdb$0
lsdb$0
:sdb$0
csli$1
lsli$1
:sli$1
csl1$1
lsl1$1
:sl1$1
csdb$1
lsdb$1
:sdb$1
csli$2
lsli$2
:sli$2
csl1$2
lsl1$2
:sl1$2
csdb$2
lsdb$2
:sdb$2
'''
        self.assertEqual(rules_truth, rules)
    
    def test_case_hashcat_chain(self):
        chain = model.Chain()
        
        strings = ['heLlo', 'worLd', 'hi']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=strings)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode(is_case=True)
        node.add_attr(model.CaseAttr(type_='Toggle', idx=3))
        chain.add_node(node)
        
        truth_words = ['heLLo', 'hi', 'world']
        result = list(chain.get_words())
        self.assertEqual(sorted(truth_words), sorted(set(result)))
        #self.assertEqual(9, chain.count_words())
        #self.assertEqual(len('\n'.join(result)+'\n'), chain.count_bytes())
    
        rules = chain.get_rules()
        self.assert_hashcat_result(truth_words, rules, basewords=strings)
        self.assertTrue(chain.check_hashcat_compatible())
        self.assertEqual('T3\n', rules)
    
    def test_add_chain(self):
        chain = model.Chain()
        
        basewords = ['heLlo', 'worLd']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=basewords)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.AddNode(prepend=False)
        node.add_attr(model.FileAttr(path=self.test_words_path))
        chain.add_node(node)
        
        node = model.AddNode(prepend=False)
        node.add_attr(model.StringListAttr(strings=['A', 'B']))
        node.add_attr(model.NothingAdderAttr())
        chain.add_node(node)
        
        truth_words = ['heLlotest1A', 'heLlotest1B', 'heLlotest1', 'heLlotest word 2A', 'heLlotest word 2B', 'heLlotest word 2', 'heLloTHIRDTESTWORDA', 'heLloTHIRDTESTWORDB', 'heLloTHIRDTESTWORD', 'worLdtest1A', 'worLdtest1B', 'worLdtest1', 'worLdtest word 2A', 'worLdtest word 2B', 'worLdtest word 2', 'worLdTHIRDTESTWORDA', 'worLdTHIRDTESTWORDB', 'worLdTHIRDTESTWORD']
        result = list(chain.get_words())
        self.assertEqual(sorted(result), sorted(truth_words))
        self.assertEqual(len(result), chain.count_words())
    
        rules = chain.get_rules()
        self.assert_hashcat_result(truth_words, rules, basewords)
        self.assertTrue(chain.check_hashcat_compatible())
    
        rules_truth = '''$t$e$s$t$1$A
$t$e$s$t$ $w$o$r$d$ $2$A
$T$H$I$R$D$T$E$S$T$W$O$R$D$A
$t$e$s$t$1$B
$t$e$s$t$ $w$o$r$d$ $2$B
$T$H$I$R$D$T$E$S$T$W$O$R$D$B
$t$e$s$t$1:
$t$e$s$t$ $w$o$r$d$ $2:
$T$H$I$R$D$T$E$S$T$W$O$R$D:
'''
        self.assertEqual(rules_truth, rules)
    
    def test_append_nothing_chain(self):
        chain = model.Chain()
        
        basewords = ['heLlo', 'worLd']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=basewords)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.AddNode(prepend=False)
        node.add_attr(model.StringListAttr(strings=['A', 'B']))
        node.add_attr(model.NothingAdderAttr())
        chain.add_node(node)
        
        truth_words = ['heLlo', 'heLloA', 'heLloB', 'worLd', 'worLdA', 'worLdB']
        result = list(chain.get_words())
        self.assertEqual(sorted(result), sorted(truth_words))
        self.assertEqual(len(result), chain.count_words())
    
        rules = chain.get_rules()
        self.assert_hashcat_result(truth_words, rules, basewords)
        self.assertTrue(chain.check_hashcat_compatible())
        rules_truth = '''$A
$B
:
'''
        self.assertEqual(rules_truth, rules)

    def test_parallel_mutator_chain(self):
        chain = model.Chain()
        
        node = model.BaseNode(is_root=True)
        attr = model.FileAttr(path=self.test_words_path)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode(is_case=True)
        
        attr = model.CaseAttr(type_='First', case='Uppercase')
        node.add_attr(attr)
        attr = model.CaseAttr(type_='Toggle', idx=3)
        node.add_attr(attr)
        
        chain.add_node(node)
        
        truth_words = ['Test1', 'tesT1',
                       'Test word 2', 'tesT word 2',
                       'THIrDTESTWORD', 'Thirdtestword']
        result = list(chain.get_words())
        self.assertEqual(sorted(truth_words), sorted(result))
        self.assertEqual(6, chain.count_words())
        self.assertEqual(64, chain.count_bytes())
        self.assertTrue(chain.check_hashcat_compatible())

    def test_nothing_mutator_chain(self):
        chain = model.Chain()
        
        node = model.BaseNode(is_root=True)
        attr = model.FileAttr(path=self.test_words_path)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode(is_case=True)
        
        attr = model.CaseAttr(type_='First', case='Uppercase')
        node.add_attr(attr)
        attr = model.NothingMutatorAttr()
        node.add_attr(attr)
        
        chain.add_node(node)
        
        truth_words = ['Test1', 'test1',
                       'Test word 2', 'test word 2',
                       'THIRDTESTWORD', 'Thirdtestword']
        result = list(chain.get_words())
        self.assertEqual(sorted(truth_words), sorted(result))
        self.assertEqual(6, chain.count_words())
        self.assertEqual(64, chain.count_bytes())
        self.assertTrue(chain.check_hashcat_compatible())
    
        rules = chain.get_rules()
        self.assert_hashcat_result(truth_words, rules)
        self.assertTrue('c\n:\n', rules)
    
    def test_substitution_mutator_chain(self):
        chain = model.Chain()
        
        basewords = ['hello', 'world']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=basewords)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode()
        attr = model.SubstitutionAttr(type_='First', checked_vals=['l -> i', 'l -> 1'], all_together=False)
        node.add_attr(attr)
        chain.add_node(node)
        
        truth_words = ['he1lo', 'heilo', 'wor1d', 'worid']
        result = list(chain.get_words())
        self.assertEqual(sorted(truth_words), sorted(result))
        # Substitution counts are over-estimated due to de-duplication
        self.assertEqual(2, chain.count_words())
        # Byte counts for multi-character replacements are estimated as if
        # they were single-character
        self.assertEqual(16, chain.count_bytes())
        self.assertFalse(chain.check_hashcat_compatible())
    
    def test_substitution_hashcat_chain(self):
        chain = model.Chain()
        
        basewords = ['hello', 'world']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=basewords)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode()
        attr = model.SubstitutionAttr(type_='All', checked_vals=['l -> i', 'o -> 0'], all_together=True)
        node.add_attr(attr)
        chain.add_node(node)
        
        truth_words = ['heii0', 'w0rid']
        result = list(chain.get_words())
        self.assertEqual(sorted(truth_words), sorted(result))
        # Substitution counts are over-estimated due to de-duplication
        self.assertEqual(2, chain.count_words())
        # Byte counts for multi-character replacements are estimated as if
        # they were single-character
        self.assertEqual(12, chain.count_bytes())
        self.assertTrue(chain.check_hashcat_compatible())
    
        rules = chain.get_rules()
        self.assert_hashcat_result(truth_words, rules, basewords)
        self.assertTrue(chain.check_hashcat_compatible())
        self.assertEqual('sliso0\n', rules)
    
    def test_empty_mutate_chain(self):
        chain = model.Chain()
        
        basewords = ['hello', 'world']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=basewords)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode()
        chain.add_node(node)
        
        result = list(chain.get_words())
        self.assertEqual(sorted(basewords), sorted(result))
        self.assertEqual(len(basewords), chain.count_words())
        self.assertEqual(len('\n'.join(result)+'\n'), chain.count_bytes())
        
        rules = chain.get_rules()
        self.assert_hashcat_result(sorted(basewords), rules, basewords=basewords)
        self.assertTrue(chain.check_hashcat_compatible())
    
        self.assertEqual(':\n', rules)
    
    def test_empty_mutate_case_chain(self):
        chain = model.Chain()
        
        basewords = ['hello', 'world']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=basewords)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.MutateNode()
        chain.add_node(node)
        
        node = model.MutateNode(is_case=True)
        attr = model.CaseAttr(type_='First', case='Uppercase')
        node.add_attr(attr)
        chain.add_node(node)
        
        truth_words = ['Hello', 'World']
        result = list(chain.get_words())
        self.assertEqual(sorted(truth_words), sorted(result))
        self.assertEqual(len(basewords), chain.count_words())
        self.assertEqual(len('\n'.join(result)+'\n'), chain.count_bytes())
        
        rules = chain.get_rules()
        self.assert_hashcat_result(sorted(truth_words), rules, basewords=basewords)
        self.assertTrue(chain.check_hashcat_compatible())
    
        self.assertEqual(':c\n', rules)
    
    def test_empty_add_case_chain(self):
        chain = model.Chain()
        
        basewords = ['hello', 'world']
        node = model.BaseNode(is_root=True)
        attr = model.StringListAttr(strings=basewords)
        node.add_attr(attr)
        chain.add_node(node)
        
        node = model.AddNode()
        chain.add_node(node)
        
        node = model.MutateNode(is_case=True)
        attr = model.CaseAttr(type_='First', case='Uppercase')
        node.add_attr(attr)
        chain.add_node(node)
        
        truth_words = ['Hello', 'World']
        result = list(chain.get_words())
        self.assertEqual(sorted(truth_words), sorted(result))
        self.assertEqual(len(basewords), chain.count_words())
        self.assertEqual(len('\n'.join(result)+'\n'), chain.count_bytes())
        
        rules = chain.get_rules()
        self.assert_hashcat_result(sorted(truth_words), rules, basewords=basewords)
        self.assertTrue(chain.check_hashcat_compatible())
    
        self.assertEqual(':c\n', rules)
    
    def test_nothing_basenode_chain(self):
        chain = model.Chain()
    
        node = model.BaseNode(is_root=True)
        attr = model.NothingAdderAttr()
        node.add_attr(attr)
        chain.add_node(node)

        node = model.AddNode(prepend=True)
        range_ = [5, 10]
        attr = model.RangeAttr(start=range_[0], end=range_[1])
        node.add_attr(attr)
        chain.add_node(node)
        
        result = list(chain.get_words())
        truth = list(map(str, range(*range_)))
        self.assertEqual(sorted(result), sorted(truth))
        self.assertEqual(len(result), chain.count_words())
        self.assertEqual(len('\n'.join(result)+'\n'), chain.count_bytes())
        self.assertTrue(chain.check_hashcat_compatible())
    
    def run_hashcat(self, rules, basewords=None):
        if basewords is None:
            basewords_path = self.test_words_path
        else:
            basewords_path = os.path.join(self.test_dir, 'hashcat_basewords')
            open(basewords_path, 'w').write('\n'.join(basewords) + '\n')
        
        out_path = os.path.join(self.test_dir, 'hashcat.out')
        rules_path = os.path.join(self.test_dir, 'hashcat.rules')
        open(rules_path, 'w').write(rules)
        args = ['hashcat', '--stdout', '-r', rules_path, '-D1',
                '--opencl-device-type', '1',
                '--outfile', out_path, basewords_path]
        #print("hashcat args:", ' '.join(args))
                
        subprocess.call(' '.join(args), shell=True, stderr=open('/dev/null', 'w'))
        return open(out_path).read().split('\n')[:-1]
    
    def assert_is_subset(self, a, b):
        for item in a:
            self.assertIn(item, b)

    def assert_hashcat_result(self, truth_words, rules, basewords=None):
        if run_hashcat_tests:
            result = self.run_hashcat(rules, basewords=basewords)
            self.assert_is_subset(truth_words, result)

    def setUp(self):
        '''
        Create temporary input files
        '''
        self.test_dir = tempfile.mkdtemp()
        self.test_words_path = os.path.join(self.test_dir, 'test_words.txt')
        
        self.test_words = ['test1', 'test word 2', 'THIRDTESTWORD']
        
        warnings.simplefilter("ignore") # open() below gives unexpected warning
        open(self.test_words_path, 'w').write('\n'.join(self.test_words))

    def tearDown(self):
        '''
        Delete all temporary files
        '''
        shutil.rmtree(self.test_dir)

if __name__ == '__main__':
    unittest.main()
