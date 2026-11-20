import React, { FunctionComponent } from 'react';
import Box from '@mui/material/Box/Box';
import Divider from '@mui/material/Divider/Divider';
import Grid from '@mui/material/Grid/Grid';
import makeStyles from '@mui/styles/makeStyles/makeStyles';

type Props = {
    mt: number;
    mb: number;
    mr?: number;
    ml?: number;
    displayTrigger: unknown;
};

const useStyles = makeStyles({ divider: { width: '100%' } });
export const HorizontalDivider: FunctionComponent<Props> = ({
    displayTrigger,
    mt = 2,
    mb = 0,
    mr = 2,
    ml = 2,
}) => {
    const classes = useStyles();
    return (
        <>
            {displayTrigger && (
                <Grid item xs={12}>
                    <Box mt={mt} mr={mr} ml={ml} mb={mb}>
                        <Divider className={classes.divider} />
                    </Box>
                </Grid>
            )}
        </>
    );
};
