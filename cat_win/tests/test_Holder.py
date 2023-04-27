from unittest import TestCase
import os

from cat_win.const.ArgConstants import *
from cat_win.util.Holder import Holder
# import sys
# sys.path.append('../cat_win')

test_file_dir = os.path.join(os.path.dirname(__file__), 'texts')
test_file_path        = os.path.join(test_file_dir, 'test.txt')
test_file_edge_case_1 = os.path.join(test_file_dir, 'test_holderEdgeCase_1.txt')
test_file_edge_case_2 = os.path.join(test_file_dir, 'test_holderEdgeCase_2.txt')
test_file_edge_case_3 = os.path.join(test_file_dir, 'test_holderEdgeCase_3.txt')
test_file_edge_case_4 = os.path.join(test_file_dir, 'test_holderEdgeCase_4.txt')
test_file_empty       = os.path.join(test_file_dir, 'test_empty.txt')
holder = Holder()


class TestHolder(TestCase):
    def tearDown(self):
        holder.args = []
        for i in range(len(holder.args_id)):
            holder.args_id[i] = False
    
    def test__calcFileLineLengthPlaceHolder__(self):
        holder.setFiles([test_file_path])
        holder.__calcFileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 2)

    def test__calcFileLineLengthPlaceHolder__Edge(self):
        holder.setFiles([test_file_edge_case_1])
        holder.__calcFileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 1)

        holder.setFiles([test_file_edge_case_2])
        holder.__calcFileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 2)
        
        holder.setFiles([test_file_edge_case_3, test_file_edge_case_4])
        holder.__calcFileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 1)
        
        holder.setFiles([test_file_edge_case_2, test_file_edge_case_4])
        holder.__calcFileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 2)
        
    def test___calcMaxLineLength___empty(self):
        self.assertEqual(holder.__calcMaxLineLength__(test_file_empty), 0)

    def test_allFilesLinesSum(self):
        holder.setFiles([test_file_path, test_file_edge_case_1])
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.allFilesLinesSum, 10)

        holder.setFiles([test_file_path] * 13)
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.allFilesLinesSum, 104)

    def test_fileLineNumberPlaceHolder(self):
        holder.setFiles([test_file_path])
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.fileLineNumberPlaceHolder, 1)

        holder.setFiles([test_file_path, test_file_path])
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.fileLineNumberPlaceHolder, 1)

        holder.setFiles([test_file_edge_case_3])
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.fileLineNumberPlaceHolder, 2)

    def test_fileNumberPlaceHolder(self):
        holder.setFiles([test_file_edge_case_1] * 9)
        holder.__calcFileNumberPlaceHolder__()
        self.assertEqual(holder.fileNumberPlaceHolder, 1)

        holder.setFiles([test_file_edge_case_1] * 10)
        holder.__calcFileNumberPlaceHolder__()
        self.assertEqual(holder.fileNumberPlaceHolder, 2)

        holder.setFiles([test_file_edge_case_1] * 99)
        holder.__calcFileNumberPlaceHolder__()
        self.assertEqual(holder.fileNumberPlaceHolder, 2)

        holder.setFiles([test_file_edge_case_1] * 100)
        holder.__calcFileNumberPlaceHolder__()
        self.assertEqual(holder.fileNumberPlaceHolder, 3)
        
    def test_setArgBase64(self):
        holder.setArgs([(ARGS_B64E, '--b64e')])
        self.assertEqual(holder.args_id[ARGS_B64E], True)
        self.assertEqual(holder.args_id[ARGS_NOCOL], True)
        self.assertEqual(holder.args_id[ARGS_LLENGTH], False)
        self.assertEqual(holder.args_id[ARGS_NUMBER], False)

    def test__getFileDisplayName(self):
        holder.setTempFileStdIn('STDINFILE')
        holder.setTempFileEcho('TEMPFILEECHO')
        holder.setFiles([test_file_edge_case_3, 'STDINFILE', test_file_edge_case_4, 'TEMPFILEECHO'])
        
        self.assertEqual(holder._getFileDisplayName('STDINFILE'), '<STDIN>')
        self.assertEqual(holder._getFileDisplayName('TEMPFILEECHO'), '<ECHO>')
        self.assertEqual(holder._getFileDisplayName(test_file_edge_case_3), test_file_edge_case_3)
        self.assertEqual(holder._getFileDisplayName(test_file_edge_case_4), test_file_edge_case_4)
        
    def test_setDecodingTempFiles(self):
        holder.setFiles([test_file_path] * 3)
        self.assertListEqual(holder._inner_files, [test_file_path] * 3)
        
        holder.setDecodingTempFiles([test_file_empty] * 4)
        self.assertListEqual(holder._inner_files, [test_file_empty] * 4)
        
    def test_addArgs(self):
        holder.setArgs([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        holder.addArgs([(ARGS_NUMBER, 'x'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(holder.args, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        self.assertEqual(holder.args_id.count(True), 2)
        
        holder.addArgs([(ARGS_TABS, 'c')])
        self.assertListEqual(holder.args, [(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b'), (ARGS_TABS, 'c')])
        self.assertEqual(holder.args_id.count(True), 3)
        
    def test_deleteArgs(self):
        holder.setArgs([(ARGS_NUMBER, 'a'), (ARGS_LLENGTH, 'b')])
        holder.deleteArgs([(ARGS_ENDS, 'a'), (ARGS_NUMBER, 'x')])
        self.assertListEqual(holder.args, [(ARGS_LLENGTH, 'b')])
        self.assertEqual(holder.args_id.count(True), 1)
        
        holder.deleteArgs([(ARGS_NUMBER, 'x'), (ARGS_LLENGTH, 'b')])
        self.assertListEqual(holder.args, [])
        self.assertEqual(holder.args_id.count(True), 0)
        