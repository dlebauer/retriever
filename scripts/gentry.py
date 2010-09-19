"""Database Toolkit for Alwyn H. Gentry Forest Transact Dataset

"""

import os
import zipfile
from .lib.tools import DbTk, DbTkTest
from .lib.models import Table
from .lib.excel import *

class main(DbTk):
    name = "Alwyn H. Gentry Forest Transact Dataset"
    shortname = "Gentry"
    url = "http://www.mobot.org/mobot/gentry/123/all_Excel.zip"
    ref = "http://www.wlbcenter.org/gentry_data.htm"
    def download(self, engine=None):
        DbTk.download(self, engine)
                
        self.engine.download_file(self.url, "all_Excel.zip")
        local_zip = zipfile.ZipFile(self.engine.format_filename("all_Excel.zip"))        
        filelist = local_zip.namelist()
        local_zip.close()
        self.engine.download_files_from_archive(self.url, filelist)
        
        filelist = [os.path.basename(filename) for filename in filelist]
        
        lines = []
        tax = []
        for filename in filelist:
            print "Extracting data from " + filename + " . . ."
            book = xlrd.open_workbook(self.engine.format_filename(filename))
            sh = book.sheet_by_index(0)
            rows = sh.nrows
            for i in range(1, rows):
                thisline = []
                row = sh.row(i)
                n = 0
                cellcount = 0
                for cell in row:
                    if not Excel.empty_cell(cell):
                        cellcount += 1 
                if cellcount > 4 and not Excel.empty_cell(row[0]):
                    try:
                        a = int(Excel.cell_value(row[0]).split('.')[0])
                        for cell in row:
                            n += 1
                            if n < 5 or n > 12:
                                if not Excel.empty_cell(cell) or n == 13:
                                    thisline.append(Excel.cell_value(cell))
                        
                        newline = [str(value).title().replace("\\", "/") for value in thisline] 
                        lines.append(newline)
                        
                        # Check how far the species is identified
                        full_id = 0
                        if len(newline[3]) < 3:
                            if len(newline[2]) < 3:
                                id_level = "family"
                            else:
                                id_level = "genus"
                        else:
                            id_level = "species"
                            full_id = 1
                        tax.append((newline[1], newline[2], newline[3], id_level, str(full_id)))
                    except:
                        pass                    
        
        tax = sorted(tax, key=lambda group: group[0] + " " + group[1] + " " + group[2])
        unique_tax = []
        tax_dict = dict()
        tax_count = 0
        
        # Get all unique families/genera/species
        for group in tax:
            if not (group in unique_tax):
                unique_tax.append(group)
                tax_count += 1
                tax_dict[group[0:3]] = tax_count
                msg = "Generating taxonomic groups: " + str(tax_count)
                print msg + "\b" * len(msg)
        
        # Create species table
        table = Table()
        table.tablename = "species"
        table.columns=[("species_id"            ,   ("pk-auto",)    ),
                       ("family"                ,   ("char", 50)    ),
                       ("genus"                 ,   ("char", 50)    ),
                       ("species"               ,   ("char", 50)    ),
                       ("id_level"              ,   ("char", 10)    ),
                       ("full_id"               ,   ("bool",)       )]

        table.source = ['::'.join([group[i] for i in range(5)]) 
                        for group in unique_tax]
        table.delimiter = '::'
        self.engine.table = table
        self.engine.create_table()
        self.engine.add_to_table()        
        
        # Create stems table
        table = Table()
        table.tablename = "stems"
        table.columns=[("stem_id"               ,   ("pk-auto",)    ),
                       ("line"                  ,   ("int",)        ),
                       ("species_id"            ,   ("int",)        ),
                       ("liana"                 ,   ("char", 10)    ),
                       ("stem"                  ,   ("double",)     )]
        table.hasindex = False
        stems = []
        for line in lines:
            species_info = [str(line[0]).split('.')[0], 
                            tax_dict[(line[1], line[2], line[3])],
                            line[4]
                            ]
            stem_count = len(line) - 5
            for i in range(stem_count):
                stem = species_info + [line[(i + 1) * -1]]
                stems.append([str(value) for value in stem])
            
        table.source = ['::'.join(stem) for stem in stems]
        table.delimiter = '::'
        self.engine.table = table
        self.engine.create_table()
        self.engine.add_to_table()
            
        return self.engine
    
    
class GentryTest(DbTkTest):
    def strvalue(self, value, col_num):
        value = DbTkTest.strvalue(self, value, col_num)
        if value[-3:] == ".00":
            value = value[0:len(value) - 3]
        return value
    def test_Gentry(self):
        DbTkTest.default_test(self,
                              [("species",
                                "8673559a7e35f1d2925d4add6d7347f7",
                                "species_id")
                              ],
                              include_pk = True)