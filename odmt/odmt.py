#!/usr/bin/python

'''
@license GPLv3
@sources https://github.com/lautr3k/odmt
@author  Sebastien Mischler <skarab>
@author  http://www.onlfait.ch
'''

import argparse, os, sys, fnmatch, ezdxf


# default i/o
inputs  = ['./input']
output = './output/merged.dxf'

# search and ignore files pattern
search = ['*.dxf']
ignore = ['*_ignore_*']

# layers indexed colors
# http://sub-atomic.com/~moses/acadcolors.html
colors = list(range(10))
colors.extend(list(range(10, 250, 10)))
colors = map(str, colors)


def file_match(inputs, patterns):
    'return if input match at least one pattern'
    for pattern in patterns:
        if fnmatch.fnmatch(inputs, pattern):
            return True
    return False

def dxf_search(inputs):
    'scan an input file or directory for DXF file'
    found   = []
    ignored = []
    if os.path.isdir(inputs):
        for file in os.listdir(inputs):
            r = dxf_search(os.path.join(inputs, file))
            found.extend(r[0])
            ignored.extend(r[1])
    elif os.path.isfile(inputs):
        if file_match(inputs, search):
            if file_match(inputs, ignore):
                ignored.append(inputs)
            else:
                found.append(inputs)
        else:
            ignored.append(inputs)
    return found, ignored

def dxf_parse(file):
    ''' 
        extract all LINE tags from an OpenSCAD DXF file 
        and return an array of POLYLINE points
    '''
    counter    = 0
    points     = []
    last_block = []
    polylines  = []

    with open(file) as f:
        for line in f:
            line = line.strip('\n');
            
            # block start
            if line == 'LINE':
                counter = 1;
                block   = [[0, 0], [0, 0]];
            
            # in the block
            if counter > 0:
                # start line
                if counter == 5:
                    block[0][0] = line
                if counter == 7:
                    block[0][1] = line
                # end line
                if counter == 9:
                    block[1][0] = line
                if counter == 11:
                    block[1][1] = line
                # increment
                counter += 1

            # end block
            if counter == 13:
                counter = 0
                
                # discontinued line
                if len(last_block) and block[0] != last_block[1]:
                    polylines.append(points)
                    points = []

                points.append((block[0][0], block[0][1]))
                points.append((block[1][0], block[1][1]))
                last_block = block
            
    # return polylines
    if len(points):
        polylines.append(points)
        return polylines

    # no polyline found
    return None

def dxf_merge(files, colors = range(0, 256), nolayers = False):
    'merge DXF file and convert continuous line to polyline.'
    
    # DXF file
    dwg = ezdxf.new('AC1015')
    msp = dwg.modelspace()

    # layer vars
    layer_num = 1

    layer_name  = 'layer0'
    layer_names = []

    layer_colors = iter(colors)
    try:
        layer_color  = next(layer_colors)
    except:
        layer_color = 0
        pass
    # for each files
    for file in files:
        # layer name
        if nolayers == False:
            layer_name = os.path.basename(file)
            n = layer_name
            i = 1
            while n in layer_names:
                n = layer_name + '_' + str(i)
                i += 1
            layer_names.append(n)
            layer_name = n

        # create layer
        if layer_num < 2 or nolayers == False:
            dwg.layers.add(
                name       = layer_name)

        # parse file
        polylines = dxf_parse(file)
        if len(polylines):
            for polyline in polylines:
                pl = [(float(p1), float(p2)) for p1,p2 in polyline]
                print(pl)
                msp.add_lwpolyline(pl)

        # next layer color
        # layer_color = next(layer_colors, False)
        # if layer_color == False:
        #     layer_colors = iter(colors)
        #     layer_color  = next(layer_colors)

        # increment layer num
        layer_num += 1

    #return the dwg object
    return dwg


def odmt_cli():
    # configuration

    global inputs, output, search, ignore, colors
    app_name        = 'odmt'
    app_version     = '1.0.0'
    app_description = 'OpenSCAD DXF Merge Tool (odmt) - v' + app_version


    # command line parser
    parser = argparse.ArgumentParser(
        prog        = app_name,
        description = app_description)
    parser.add_argument('--inputs', '-i',
        nargs   = '+',
        default = inputs,
        metavar = 'path',
        help    = 'input file or directory - default: ['
                    + ', '.join(inputs) + ']')
    parser.add_argument('--output', '-o',
        default = output,
        metavar = 'path',
        help    = 'output file - default: ' + output)
    parser.add_argument('--search',
        nargs   = '+',
        default = search,
        metavar = 'pattern',
        help    = 'search file pattern - default: ['
                    + ', '.join(search) + ']')
    parser.add_argument('--ignore',
        nargs   = '+',
        default = ignore,
        metavar = 'pattern',
        help    = 'ignored file/directory pattern - default: ['
                    + ', '.join(ignore) + ']')
    parser.add_argument('--colors',
        nargs   = '+',
        default = colors,
        metavar = 'index',
        help    = 'layers indexed colors - default: ['
                    + ', '.join(colors) + ']')
    parser.add_argument('--nolayers',
        action = 'store_true',
        help   = 'if set, all files will be merged into the same layer')
    parser.add_argument('--version', '-v',
        action  = 'version',
        version = '%(prog)s ' + app_version)

    # parse the command line
    args = parser.parse_args()

    # local variables assignment
    inputs    = args.inputs
    output   = os.path.realpath(args.output)
    search   = args.search
    ignore   = args.ignore
    colors   = map(int, args.colors)
    nolayers = args.nolayers

    # test output directory
    output_dir = os.path.dirname(output)

    if os.path.isdir(output_dir) == False:
        print('output directory not found :', output_dir)
        sys.exit(1);

    # DXF files
    input_files   = []
    ignored_files = []

    # make the files tree
    for item in inputs:
        result = dxf_search(os.path.realpath(item))
        input_files.extend(result[0])
        ignored_files.extend(result[1])

    # do the serious job
    dxf_merge(input_files, colors, nolayers).saveas(output)

    # success message
    print('inputs   :', '\n\t  '.join(input_files))
    if len(ignored_files):
        print('\nignored :', '\n\t  '.join(ignored_files))
    print('\noutput  :', output)

if __name__=="__main__":
    main()
