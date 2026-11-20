import React, { FunctionComponent } from 'react';

import TableCell from '@mui/material/TableCell/TableCell';
import TableHead from '@mui/material/TableHead/TableHead';
import TableRow from '@mui/material/TableRow/TableRow';
import makeStyles from '@mui/styles/makeStyles/makeStyles';
import { useSafeIntl } from 'bluesquare-components';

import MESSAGES from '../../../constants/messages';

const useStyles = makeStyles(() => ({
    tableCellHead: {
        fontWeight: 'bold',
    },
    tableCellHeadNoPadding: {
        fontWeight: 'bold',
        paddingLeft: 0,
    },
}));

export const Head: FunctionComponent = () => {
    const { formatMessage } = useSafeIntl();
    const classes: Record<string, string> = useStyles();

    return (
        <TableHead>
            <TableRow>
                <TableCell width={150} className={classes.tableCellHead}>
                    {formatMessage(MESSAGES.label)}
                </TableCell>
                <TableCell className={classes.tableCellHeadNoPadding}>
                    {formatMessage(MESSAGES.value)}
                </TableCell>
            </TableRow>
        </TableHead>
    );
};
