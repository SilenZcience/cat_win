from cat_win.util.Holder import Holder
from cat_win.const.ArgConstants import *
from unittest import TestCase
import os
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
    def test__calcfileLineLengthPlaceHolder__(self):
        holder.setFiles([test_file_path])
        holder.__calcfileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 2)

    def test__calcfileLineLengthPlaceHolder__Edge(self):
        holder.setFiles([test_file_edge_case_1])
        holder.__calcfileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 1)

        holder.setFiles([test_file_edge_case_2])
        holder.__calcfileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 2)
        
        holder.setFiles([test_file_edge_case_3, test_file_edge_case_4])
        holder.__calcfileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 1)
        
        holder.setFiles([test_file_edge_case_2, test_file_edge_case_4])
        holder.__calcfileLineLengthPlaceHolder__()
        self.assertEqual(holder.fileLineLengthPlaceHolder, 2)
        
    def test___calcMaxLine___empty(self):
        self.assertEqual(holder.__calcMaxLine__(test_file_empty), 0)

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

    def test_getAppliedFiles(self):
        expexted_output = [(test_file_edge_case_3, test_file_edge_case_3),
                           ('STDINFILE', '<STDIN>'),
                           (test_file_edge_case_4, test_file_edge_case_4),
                           ('TEMPFILEECHO', '<ECHO>')]
        holder.setFiles([test_file_edge_case_3, 'STDINFILE', test_file_edge_case_4, 'TEMPFILEECHO'])
        holder.setTempFileStdIn('STDINFILE')
        holder.setTempFileEcho('TEMPFILEECHO')
        
        self.assertListEqual(holder.getAppliedFiles(), expexted_output)