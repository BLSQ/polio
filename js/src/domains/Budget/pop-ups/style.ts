import makeStyles from '@mui/styles/makeStyles/makeStyles';

const actionStyles = theme => ({
    action: {
        paddingBottom: theme.spacing(2),
        paddingRight: theme.spacing(2),
    },
});

export const useDialogActionStyles = makeStyles(actionStyles);
