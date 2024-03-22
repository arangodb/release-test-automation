#!/usr/bin/env python3
"""write a nice ascii table with results"""
from pathlib import Path
from pprint import pprint
from beautifultable import BeautifulTable, ALIGN_LEFT

def write_table(results, statusFile=False):
    """write a nice ascii table with results"""
    try:
        status = True
        table = BeautifulTable(maxwidth=140)
        for one_suite_result in results:
            if len(one_suite_result) > 0:
                for one_result in one_suite_result:
                    if one_result["success"]:
                        table.rows.append(
                            [
                                one_result["testrun name"],
                                one_result["testscenario"],
                                # one_result['success'],
                                ("\n".join(one_result["messages"])).replace('\t', '    '),
                            ]
                        )
                    else:
                        table.rows.append(
                            [
                                one_result["testrun name"],
                                one_result["testscenario"],
                                # one_result['success'],
                                ("\n".join(one_result["messages"]) + "\n" + "H" *
                                 40 + "\n" + one_result["progress"]).replace(
                                     '\t', '    '),
                            ]
                        )
                    status = status and one_result["success"]
        table.columns.header = [
            "Testrun",
            "Test Scenario",
            # 'success', we also have this in message.
            "Message + Progress",
        ]
        table.columns.alignment["Message + Progress"] = ALIGN_LEFT

        tablestr = str(table)
        Path("testfailures.txt").write_text(tablestr, encoding="utf8")
        if statusFile:
            Path("status.json").write_text("true" if status else "false", encoding="utf8")
        print(tablestr)
        return status
    except Exception as ex:
        if statusFile:
            Path("status.json").write_text("false", encoding="utf8")
        print("Write result table has thrown!")
        print(ex)
        pprint(results)
        raise ex
