import os
import sys
import webbrowser
from collections import defaultdict
from sys import exit, stderr

def generate_head():
    print('<head>\n')
    print('<style>\n')
    print('.aws-table th {border: none; border-collapse: collapse; border-radius: 10px; background-color: #f1f1f1; '
        + 'font-family: Arial; font-size: 20px; padding: 10px; text-align: center; table-layout:fixed;}\n')
    print('.aws-table td {border: none; border-collapse: collapse; border-radius: 10px; background-color: #f1f1f1; '
        + 'text-align: center; table-layout:fixed;}\n')
    print('.aws-table .service {border: none; border-collapse: collapse; font-family: Arial; '
        + 'font-size: 18px; text-align: center; table-layout:fixed; background-color: #f1f1f1;}\n')
    print('.nfound {border: 10px solid Orange; border-radius: 10px; padding: 10px;}\n')
    print('.found {border: 10px solid LightGreen; border-radius: 10px; padding: 10px;}\n')
    print('.error {border: 10px solid Red; border-radius: 10px; padding: 10px;}\n')
    print('.denied {border: 10px solid Blue; border-radius: 10px; padding: 10px;}\n')
    print('.nCollapse {background-color: Orange; border-radius: 10px; color: white; cursor: pointer; '
        + 'padding: 14px; width: 450px; border: none; text-align: center; font-size: 20px;}\n')
    print('.fCollapse {background-color: LightGreen; border-radius: 10px; color: white; cursor: pointer; '
        + 'padding: 14px; width: 450px; border: none; text-align: center; font-size: 20px;}\n')
    print('.eCollapse {background-color: Red; border-radius: 10px; color: white; cursor: pointer; '
        + 'padding: 14px; width: 450px; border: none; text-align: center; font-size: 20px;}\n')
    print('.dCollapse {background-color: Blue; border-radius: 10px; color: white; cursor: pointer; '
        + 'padding: 14px; width: 450px; border: none; text-align: center; font-size: 20px;}\n')
    print('.active, .nCollapse:hover {width: 450px; background-color: #777;}\n')
    print('.active, .fCollapse:hover {width: 450px; background-color: #777;}\n')
    print('.active, .eCollapse:hover {width: 450px; background-color: #777;}\n')
    print('.active, .dCollapse:hover {width: 450px; background-color: #777;}\n')
    print('.content {display: none; overflow: hidden; width: 450px; background-color: #f1f1f1;}\n')

    print('#searchInput {\n')
    print('  background-position: 10px 10px;\n')
    print('  background-repeat: no-repeat;\n')
    print('  width: 300px;\n')
    print('  font-size: 16px;\n')
    print('  padding: 12px 20px 12px 40px;\n')
    print('  border: 1px solid #ddd;\n')
    print('  margin-bottom: 12px;\n')
    print('}\n')
    print('</style>\n')
    print('</head>\n')


def generate_table(results_by_region, services_in_grid):
    print('<table class="aws-table"; id="mainTable"; table-layout:fixed;>')
    print('    <tr>\n')
    print('        <th>Service</th>\n')
    for region_column in sorted(results_by_region):
        print('<th >' + str(region_column) + '</th>\n')
    print('    </tr>\n')
    rest_by_type = defaultdict(list)
    for service_type in sorted(services_in_grid):
        print('    <tr>\n')
        print('        <td class="service">' + service_type + '</td>\n')
        for result_region in sorted(results_by_region):
            print('        <td width="450">\n')
            for result_type in ('---', '+++', '>:|', '!!!'):
                empty_type = True
                result_type_list = list(filter(lambda x: x[1] == service_type, sorted(results_by_region[result_region][result_type])))
                result_type_count = ' [' + str(len(result_type_list)) + ']'
                for result in result_type_list:
                    if empty_type:
                        print('        <button type="button" class="' + status_switch(result_type + 'col') + '">'
                            + status_switch(result_type + 'box') + result_type_count + '</button>\n')
                        print('        <div class="content">\n')
                        empty_type = False
                    print('<div class="' + status_switch(result_type) + '">')
                    print(str(result[3]))
                    print('<br></div>')
                if not(empty_type):
                    print('        </div>')
            print('        </td>')
        print('    </tr>\n')
    print('</table>')


def generate_collapsibles():
    print('var coll = document.querySelectorAll(".nCollapse,.fCollapse,.eCollapse,.dCollapse");')
    print('var i;\n')
    print('for (i = 0; i < coll.length; i++) {\n')
    print('  coll[i].addEventListener("click", function() {\n')
    print('    this.classList.toggle("active");\n')
    print('    var content = this.nextElementSibling;\n')
    print('    if (content.style.display === "block") {\n')
    print('      content.style.display = "none";\n')
    print('    } else {\n')
    print('      content.style.display = "block";\n')
    print('    }\n')
    print('  });\n')
    print('}\n')


def generate_searchfunc():
    print('function search() {\n')
    print('  var input, filter, table, box, btn, count, el, i, j, btnText, txtValue;\n')
    print('  input = document.getElementById("searchInput");\n')
    print('  filter = input.value.toUpperCase();\n')
    print('  table = document.getElementById("mainTable");\n')
    print("  box = table.querySelectorAll('.content');\n")
    print("  btn = table.querySelectorAll('[type=button]');\n")
    print('  for (i = 0; i < box.length; i++) {\n')

    print("    el = box[i].querySelectorAll('.nfound, .found, .error, .denied');\n")
    print('    count = 0;\n')
    print('    for (j = 0; j < el.length; j++) {\n')
    print('      txtValue = el[j].textContent || el[j].innerText;\n')
    print('      if (txtValue.toUpperCase().indexOf(filter) > -1) {\n')
    print('        el[j].style.display = "";\n')
    print('        count++;\n')
    print('      } else {\n')
    print('        el[j].style.display = "none";\n')
    print('      }\n')
    print('    }\n')
    print('    btnText = btn[i].textContent;\n')
    print('    btn[i].textContent = btnText.substring(0, btnText.indexOf("[") + 1) + count + "]";\n')

    print('  }\n')
    print('}\n')


def status_switch(arg):
    switcher = {
        '---': 'nfound',
        '+++': 'found',
        '!!!': 'error',
        '>:|': 'denied',
        '---box': 'No Resources Found',
        '+++box': 'Resources Found',
        '!!!box': 'Error During Query',
        '>:|box': 'Missing Permissions',
        '---col': 'nCollapse',
        '+++col': 'fCollapse',
        '!!!col': 'eCollapse',
        '>:|col': 'dCollapse'
    }
    return switcher.get(arg, '')