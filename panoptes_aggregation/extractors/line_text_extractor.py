'''
Line Tool for Text ExtractorTest
--------------------------------
This module provides a function to extract panoptes annotations
from projects using a line tool to mark lines of text in a
transcribed document and provide the text as a sub-task.
'''
from collections import OrderedDict
import copy
import numpy as np
from .extractor_wrapper import extractor_wrapper


@extractor_wrapper
def line_text_extractor(classification):
    '''Extract annotations from a line tool with a text sub-task

    Parameters
    ----------
    classification : dict
        A dictionary containing an `annotations` key that is a list of
        panoptes annotations

    Returns
    -------
    extraction : dict
        A dictionary with one key for each `frame`. The value for each frame
        is a dict with `text`, a list-of-lists of transcribe lines, `points`, a
        dict with the list-of-lists of `x` and `y` postions of each line,
        and `slope`, a list of the slopes (in deg) of each line drawn.
        For `points` and `text` there is one inner list for each annotaiton made
        on the frame.
    '''
    blank_frame = OrderedDict([
        ('points', OrderedDict([('x', []), ('y', [])])),
        ('text', []),
        ('slope', [])
    ])
    extract = OrderedDict()
    annotation = classification['annotations'][0]
    for value in annotation['value']:
        frame = 'frame{0}'.format(value['frame'])
        extract.setdefault(frame, copy.deepcopy(blank_frame))
        text = value['details'][0]['value']
        x = [value['x1'], value['x2']]
        y = [value['y1'], value['y2']]
        if (len(x) > 1) and (not np.isclose(x[0], x[-1], atol=0.01)):
            fit = np.polyfit(x, y, 1)
            y_fit = np.polyval(fit, [x[0], x[-1]])
            dx = x[-1] - x[0]
            dy = y_fit[-1] - y_fit[0]
            slope = np.rad2deg(np.arctan2(dy, dx))
        else:
            # default the slope to 0 if only one point was drawn
            slope = 0
        extract[frame]['text'].append([text])
        extract[frame]['points']['x'].append(x)
        extract[frame]['points']['y'].append(y)
        extract[frame]['slope'].append(slope)
    return extract