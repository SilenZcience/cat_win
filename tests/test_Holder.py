from cat_win.util.Holder import Holder
from unittest import TestCase
import os
# import sys
# sys.path.append("../cat_win")

test_file_dir = os.path.dirname(__file__) + '/texts/'
test_file_path = test_file_dir + "test.txt"
test_file_edge_case_1 = test_file_dir + "test_holderEdgeCase_1.txt"
test_file_edge_case_2 = test_file_dir + "test_holderEdgeCase_2.txt"
test_file_edge_case_3 = test_file_dir + "test_holderEdgeCase_3.txt"
holder = Holder()


class TestConverter(TestCase):
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
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.fileNumberPlaceHolder, 1)

        holder.setFiles([test_file_edge_case_1] * 10)
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.fileNumberPlaceHolder, 2)

        holder.setFiles([test_file_edge_case_1] * 99)
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.fileNumberPlaceHolder, 2)

        holder.setFiles([test_file_edge_case_1] * 100)
        holder.__calcPlaceHolder__()
        self.assertEqual(holder.fileNumberPlaceHolder, 3)
