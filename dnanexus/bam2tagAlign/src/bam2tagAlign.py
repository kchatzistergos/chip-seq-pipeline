#!/usr/bin/env python2
# bam2tagalign 0.0.1
# Generated by dx-app-wizard.
#
# Basic execution pattern: Your app will run on a single machine from
# beginning to end.
#
# See https://wiki.dnanexus.com/Developer-Portal for documentation and
# tutorials on how to modify this file.
#
# DNAnexus Python Bindings (dxpy) documentation:
#   http://autodoc.dnanexus.com/bindings/python/current/

import subprocess
import shlex
import dxpy
import common
from multiprocessing import cpu_count
import logging

logger = logging.getLogger(__name__)
logger.addHandler(dxpy.DXLogHandler())
logger.propagate = False


@dxpy.entry_point('main')
def main(input_bam, paired_end):

    input_bam_file = dxpy.DXFile(input_bam)

    input_bam_filename = input_bam_file.name
    input_bam_basename = input_bam_file.name.rstrip('.bam')
    dxpy.download_dxfile(input_bam_file.get_id(), input_bam_filename)

    intermediate_TA_filename = input_bam_basename + ".tagAlign"
    if paired_end:
        end_infix = 'PE2SE'
    else:
        end_infix = 'SE'
    final_TA_filename = input_bam_basename + '.' + end_infix + '.tagAlign.gz'

    subprocess.check_output('ls -l', shell=True)

    # ===================
    # Create tagAlign file
    # ===================
    out, err = common.run_pipe([
        "bamToBed -i %s" % (input_bam_filename),
        r"""awk 'BEGIN{OFS="\t"}{$4="N";$5="1000";print $0}'""",
        "tee %s" % (intermediate_TA_filename),
        "gzip -cn"],
        outfile=final_TA_filename)

    subprocess.check_output('ls -l', shell=True)

    # ================
    # Create BEDPE file
    # ================
    if paired_end:
        final_nmsrt_bam_prefix = input_bam_basename + ".nmsrt"
        final_nmsrt_bam_filename = final_nmsrt_bam_prefix + ".bam"
        command = \
            "samtools sort -@ %d -n %s %s" \
            % (cpu_count(), input_bam_filename, final_nmsrt_bam_prefix)
        logger.info(command)
        subprocess.check_call(shlex.split(command))

        final_BEDPE_filename = input_bam_basename + ".bedpe.gz"
        out, err = common.run_pipe([
            "bamToBed -bedpe -mate1 -i %s" % (final_nmsrt_bam_filename),
            "gzip -cn"],
            outfile=final_BEDPE_filename)

    subprocess.check_output('ls -l', shell=True)

    tagAlign_file = dxpy.upload_local_file(final_TA_filename)
    if paired_end:
        BEDPE_file = dxpy.upload_local_file(final_BEDPE_filename)

    output = {}
    output["tagAlign_file"] = dxpy.dxlink(tagAlign_file)
    if paired_end:
        output["BEDPE_file"] = dxpy.dxlink(BEDPE_file)

    return output

dxpy.run()
