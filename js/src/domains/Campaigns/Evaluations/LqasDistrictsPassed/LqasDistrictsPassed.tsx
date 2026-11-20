import React, { FunctionComponent } from 'react';
import Box from '@mui/material/Box/Box';
import Divider from '@mui/material/Divider/Divider';
import Grid from '@mui/material/Grid/Grid';
import Typography from '@mui/material/Typography/Typography';
import { useSafeIntl } from 'bluesquare-components';
import { Nullable } from '../../../../../../../../hat/assets/js/apps/Iaso/types/utils';
import MESSAGES from '../../../../constants/messages';

type Props = {
    lqasDistrictsPassing?: Nullable<number>;
    lqasDistrictsFailing?: Nullable<number>;
};

export const LqasDistrictsPassed: FunctionComponent<Props> = ({
    lqasDistrictsPassing,
    lqasDistrictsFailing,
}) => {
    const { formatMessage } = useSafeIntl();
    return (
        <>
            <Divider />
            <Box ml={2} mb={2} mt={2}>
                <Grid container justifyContent="flex-start">
                    <Grid item xs={6} lg={5}>
                        <Typography variant="button">
                            {`${formatMessage(
                                MESSAGES.lqas_district_passing,
                            )}: `}
                        </Typography>
                    </Grid>
                    <Grid item xs={6} lg={7}>
                        <Typography variant="button">
                            {`${lqasDistrictsPassing ?? '--'}`}
                        </Typography>
                    </Grid>
                </Grid>
            </Box>
            <Box ml={2} mb={2} mt={2}>
                <Grid container>
                    <Grid item xs={6} lg={5}>
                        <Typography variant="button">
                            {`${formatMessage(
                                MESSAGES.lqas_district_failing,
                            )}: `}
                        </Typography>
                    </Grid>
                    <Grid item xs={6} lg={7}>
                        <Typography variant="button">
                            {`${lqasDistrictsFailing ?? '--'}`}
                        </Typography>
                    </Grid>
                </Grid>
            </Box>
            <Box mb={2}>
                <Divider />
            </Box>
        </>
    );
};
