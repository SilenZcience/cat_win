from unittest import TestCase
import os

from cat_win.util.strings import get_strings
# import sys
# sys.path.append('../cat_win')


test_file_dir = os.path.join(os.path.dirname(__file__), 'resources')
test_file_path = os.path.join(test_file_dir, 'test.bin')
with open(test_file_path, 'r', encoding='utf-8', errors='replace') as raw_f:
    test_content = [('', line) for line in raw_f.read().splitlines()]

class TestFile(TestCase):
    def test_get_strings_default(self):
        # unix : "strings test.bin"
        c_output = """/lib64/ld-linux-x86-64.so.2
__cxa_finalize
__libc_start_main
puts
libc.so.6
GLIBC_2.2.5
GLIBC_2.34
_ITM_deregisterTMCloneTable
__gmon_start__
_ITM_registerTMCloneTable
PTE1
u+UH
hello world
:*3$"
GCC: (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0
Scrt1.o
__abi_tag
crtstuff.c
deregister_tm_clones
__do_global_dtors_aux
completed.0
__do_global_dtors_aux_fini_array_entry
frame_dummy
__frame_dummy_init_array_entry
test.c
__FRAME_END__
_DYNAMIC
__GNU_EH_FRAME_HDR
_GLOBAL_OFFSET_TABLE_
__libc_start_main@GLIBC_2.34
_ITM_deregisterTMCloneTable
puts@GLIBC_2.2.5
_edata
_fini
__data_start
__gmon_start__
__dso_handle
_IO_stdin_used
_end
__bss_start
main
__TMC_END__
_ITM_registerTMCloneTable
__cxa_finalize@GLIBC_2.2.5
_init
.symtab
.strtab
.shstrtab
.interp
.note.gnu.property
.note.gnu.build-id
.note.ABI-tag
.gnu.hash
.dynsym
.dynstr
.gnu.version
.gnu.version_r
.rela.dyn
.rela.plt
.init
.plt.got
.plt.sec
.text
.fini
.rodata
.eh_frame_hdr
.eh_frame
.init_array
.fini_array
.dynamic
.data
.bss
.comment"""
        output = get_strings(test_content, 4, '\n')
        self.assertEqual(c_output, '\n'.join(map(lambda x: x[1], output)))

    def test_get_strings_long(self):
        # unix : "strings test.bin -n 20"
        c_output = """/lib64/ld-linux-x86-64.so.2
_ITM_deregisterTMCloneTable
_ITM_registerTMCloneTable
GCC: (Ubuntu 11.4.0-1ubuntu1~22.04) 11.4.0
deregister_tm_clones
__do_global_dtors_aux
__do_global_dtors_aux_fini_array_entry
__frame_dummy_init_array_entry
_GLOBAL_OFFSET_TABLE_
__libc_start_main@GLIBC_2.34
_ITM_deregisterTMCloneTable
_ITM_registerTMCloneTable
__cxa_finalize@GLIBC_2.2.5"""
        output = get_strings(test_content, 20, '\n')
        self.assertEqual(c_output, '\n'.join(map(lambda x: x[1], output)))
