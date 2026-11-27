import React, { FunctionComponent } from 'react';
import Box from '@mui/material/Box/Box';
import Grid from '@mui/material/Grid/Grid';
import Typography from '@mui/material/Typography/Typography';
import makeStyles from '@mui/styles/makeStyles/makeStyles';
import { useSafeIntl } from 'bluesquare-components';
import MESSAGES from '../../../../constants/messages';

const style = theme => ({
    paper: {
        marginBottom: theme.spacing(1),
        marginTop: theme.spacing(1),
        paddingTop: '5px',
        paddingBottom: '5px',
    },
    centerText: { textAlign: 'center' },
    justifyCenter: { justifyContent: 'center' },
    boldText: { fontWeight: 'bold' },
});
// @ts-ignore
const useStyles = makeStyles(style);

export const NoData: FunctionComponent = () => {
    const { formatMessage } = useSafeIntl();
    const classes = useStyles();
    return (
        <Grid container direction="column" className={classes.centerText}>
            <Grid item>
                <Box mt={4} mb={4}>
                    <Typography variant="h6" className={classes.boldText}>
                        {formatMessage(MESSAGES.noDataFound)}
                    </Typography>
                </Box>
            </Grid>
        </Grid>
    );
};
