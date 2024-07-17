from functional import seq
from typing import TextIO, Optional
import click
import json


def result_to_bounds(res: dict):
    w = res["original_width"] / 100
    h = res["original_height"] / 100
    val = res["value"]
    return {
        "x": int(float(val["x"]) * w),
        "y": int(float(val["y"]) * h),
        "width": int(float(val["width"]) * w),
        "height": int(float(val["height"]) * h),
    }


@click.command()
@click.argument("file", type=click.File("r"))
@click.option("-o", "--output", type=click.File("w"))
def labels(file: TextIO, output: Optional[TextIO]):
    with file:
        data = json.load(file)

    result = {}
    for entry in data:
        frame = entry["file_upload"].split("-")[-1]
        boxes = (seq(entry["annotations"])
                 .filter_not(lambda a: a["was_cancelled"])
                 .flat_map(lambda a: a["result"])
                 .map(lambda r: result_to_bounds(r))).to_list()
        if not boxes:
            continue
        assert len(boxes) == 2

        bottom, top = boxes
        result[frame] = {"top": top, "bottom": bottom}

    if output:
        json.dump(result, output)
    else:
        print(output)
